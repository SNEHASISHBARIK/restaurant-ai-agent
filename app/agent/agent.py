import json, logging, re, time
from uuid import uuid4
from sqlalchemy.orm import Session
try:
    from openai import OpenAI
except ImportError:
    OpenAI = None
from app.agent.router import route_message, extract_order_id
from app.agent.schemas import ChatRequest, ChatResponse, ComplaintClassification, TicketCreateRequest
from app.agent.prompts import SYSTEM_PROMPT
from app.database.models import Conversation
from app.tools.order_tools import get_order_status, get_order_details, owned_order_id, latest_order_id
from app.workflows.complaint_workflow import apply_priority_rules, RESPONSE_TARGETS
from app.tools.ticket_tools import create_support_ticket, make_idempotency_key
from app.rag.retriever import LocalVectorStore
from app.utils.config import get_settings
from app.utils.errors import LLMServiceError, OrderNotFoundError, UnauthorizedOrderError, InvalidOrderIdError, ToolExecutionError

logger = logging.getLogger(__name__)
ALLOWED_TOOLS = {"get_order_status", "get_order_details", "create_support_ticket"}

class Agent:
    def __init__(self, db: Session, rag: LocalVectorStore):
        self.db, self.rag, self.settings = db, rag, get_settings()
        self.client = OpenAI(api_key=self.settings.openai_api_key, timeout=self.settings.llm_timeout_seconds) if (self.settings.openai_api_key and OpenAI is not None) else None

    def _history(self, req: ChatRequest) -> list[dict]:
        row = self.db.get(Conversation, req.session_id)
        if not row:
            row = Conversation(session_id=req.session_id, customer_id=req.customer_id, messages="[]")
            self.db.add(row); self.db.commit()
        elif row.customer_id != req.customer_id:
            return []
        return json.loads(row.messages)[-8:]

    def _save_history(self, req: ChatRequest, history: list[dict], answer: str):
        row = self.db.get(Conversation, req.session_id)
        if not row or row.customer_id != req.customer_id: return
        history = (history + [{"role":"user","content":req.message},{"role":"assistant","content":answer}])[-8:]
        row.messages = json.dumps(history); self.db.commit()

    def _classify_complaint(self, text: str) -> ComplaintClassification:
        t = text.lower()
        category = "Payment" if any(x in t for x in ["payment", "paid", "charged", "deducted", "twice", "double", "duplicate", "overcharg"]) else "Delivery" if any(x in t for x in ["late", "delay", "delivery", "never arrived", "not delivered"]) else "Refund" if "refund" in t else "Technical" if any(x in t for x in ["app", "website", "error", "technical"]) else "Order"
        sentiment = "Negative" if any(x in t for x in ["failed", "wrong", "late", "deducted", "bad", "problem", "issue", "angry"]) else "Neutral"
        priority = "Low"
        summary = text.strip()[:450]
        if self.client:
            try:
                resp = self.client.beta.chat.completions.parse(
                    model=self.settings.openai_model,
                    messages=[{"role":"system","content":"Classify the complaint. Return only the requested structured fields. Do not invent facts."},{"role":"user","content":text}],
                    response_format=ComplaintClassification,
                )
                parsed = resp.choices[0].message.parsed
                if parsed: return apply_priority_rules(parsed, text)
            except Exception as exc:
                logger.warning("LLM classification failed; using safe local classification: %s", type(exc).__name__)
        return apply_priority_rules(ComplaintClassification(category=category, priority=priority, sentiment=sentiment, summary=summary), text)

    @staticmethod
    def _order_id_from_history(history: list[dict]) -> str | None:
        for msg in reversed(history):
            found = extract_order_id(msg.get("content", ""))
            if found: return found
        return None

    def _rag(self, text: str):
        results = self.rag.search(text)
        if not results:
            return None, []
        # One sentence per line so long policies stay readable in the chat UI.
        answer = "\n".join(re.split(r"(?<=[.!?])\s+", results[0]["text"].replace("# ", "").strip()))
        return answer, list(dict.fromkeys(r["source"] for r in results))

    def chat(self, req: ChatRequest, request_id: str | None = None) -> ChatResponse:
        request_id = request_id or f"REQ-{uuid4().hex[:12].upper()}"
        history = self._history(req)
        intent = route_message(req.message)
        tool_calls = []
        source = "direct"
        docs = []
        ticket_id = category = priority = None
        start = time.perf_counter()
        try:
            if intent in {"order_status", "order_details"}:
                order_id = extract_order_id(req.message) or self._order_id_from_history(history)
                if not order_id:
                    answer = "Please provide your order ID, for example ORD-1005."
                    return self._finish(req, history, answer, request_id, intent, source, tool_calls, docs)

            if intent == "order_status":
                try:
                    t = time.perf_counter(); data = get_order_status(self.db, order_id, req.customer_id)
                    tool_calls.append({"tool":"get_order_status","success":True,"duration_ms":round((time.perf_counter()-t)*1000,2)})
                    source = "tool"
                    answer = f"Order {data['order_id']} is currently {data['status']}. Estimated delivery: {data['estimated_delivery']}."
                except Exception as exc:
                    tool_calls.append({"tool":"get_order_status","success":False})
                    if isinstance(exc, (OrderNotFoundError, UnauthorizedOrderError, InvalidOrderIdError)):
                        answer = str(exc)
                    else:
                        logger.exception("Order status tool failed")
                        answer = "I'm unable to retrieve the current order status right now. Please try again shortly."
                return self._finish(req, history, answer, request_id, intent, source, tool_calls, docs)

            if intent == "order_details":
                try:
                    t=time.perf_counter(); data=get_order_details(self.db, order_id, req.customer_id)
                    tool_calls.append({"tool":"get_order_details","success":True,"duration_ms":round((time.perf_counter()-t)*1000,2)})
                    source="tool"
                    answer=f"Order {data['order_id']} contains: {', '.join(data['items'])}. Total: ₹{data['total_amount']:.2f}. Status: {data['status']}."
                except Exception as exc:
                    tool_calls.append({"tool":"get_order_details","success":False})
                    answer = str(exc) if isinstance(exc, (OrderNotFoundError, UnauthorizedOrderError, InvalidOrderIdError)) else "I'm unable to retrieve the order details right now. Please try again shortly."
                return self._finish(req, history, answer, request_id, intent, source, tool_calls, docs)

            if intent == "rag":
                try:
                    answer, docs = self._rag(req.message)
                    source = "knowledge_base"
                    if not answer: answer = "I couldn't find this information in the restaurant knowledge base."
                except Exception:
                    logger.exception("RAG retrieval failed")
                    answer = "I couldn't retrieve the restaurant knowledge base right now. Please try again shortly."
                return self._finish(req, history, answer, request_id, intent, source, tool_calls, docs)

            if intent == "complaint":
                classification = self._classify_complaint(req.message)
                # Only link orders that belong to this customer; never store someone else's order ID.
                order_id = owned_order_id(self.db, extract_order_id(req.message) or self._order_id_from_history(history), req.customer_id)
                if not order_id:
                    order_id = latest_order_id(self.db, req.customer_id, active_only=(classification.category == "Delivery"))
                key = make_idempotency_key(req.customer_id, order_id, classification.summary)
                ticket_req = TicketCreateRequest(customer_id=req.customer_id, order_id=order_id, category=classification.category, priority=classification.priority, sentiment=classification.sentiment, summary=classification.summary, description=req.message, idempotency_key=key)
                t=time.perf_counter(); ticket=create_support_ticket(self.db, ticket_req)
                tool_calls.append({"tool":"create_support_ticket","success":True,"duration_ms":round((time.perf_counter()-t)*1000,2)})
                source="tool"
                ticket_id=ticket.ticket_id; category=ticket.category; priority=ticket.priority
                linked = f" It's linked to order {ticket.order_id}." if ticket.order_id else " If you share your order ID, please include it in your next message."
                answer=(f"I'm sorry about that. I've created support ticket {ticket.ticket_id} for your {ticket.category.lower()} issue "
                        f"(priority: {ticket.priority}).{linked} Our team aims to respond within {RESPONSE_TARGETS[ticket.priority]}.")
                return self._finish(req, history, answer, request_id, intent, source, tool_calls, docs, ticket_id, category, priority)

            # General answer: use LLM if configured, otherwise safe short response.
            if self.client:
                try:
                    messages=[{"role":"system","content":SYSTEM_PROMPT}] + history + [{"role":"user","content":req.message}]
                    resp=self.client.chat.completions.create(model=self.settings.openai_model, messages=messages, temperature=0.1)
                    answer=resp.choices[0].message.content or "I don't have enough information to answer that."
                except Exception:
                    logger.exception("LLM general response failed")
                    answer="I’m unable to answer that right now. I can help with orders, restaurant policies, or support issues."
            else:
                answer="I can help with order status, order details, restaurant policies, and support issues."
            return self._finish(req, history, answer, request_id, intent, source, tool_calls, docs)
        finally:
            logger.info("request_id=%s intent=%s tools=%s latency_ms=%.2f", request_id, intent, [x['tool'] for x in tool_calls], (time.perf_counter()-start)*1000)

    def _finish(self, req, history, answer, request_id, intent, source, tool_calls, docs, ticket_id=None, category=None, priority=None):
        self._save_history(req, history, answer)
        return ChatResponse(request_id=request_id, answer=answer, intent=intent, source=source, tool_calls=tool_calls, documents=docs, ticket_id=ticket_id, category=category, priority=priority)
