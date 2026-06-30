"""
LangGraph - مثال کاربردی: عامل (Agent) تریاژ خرابی تجهیزات پتروشیمی
=====================================================================
سناریو:
یک اپراتور/سرپرست نگهداری یک گزارش متنی از وضعیت یک تجهیز می‌دهد
(مثلاً افزایش دما یا ویبراسیون پمپ). عامل با استفاده از چند ابزار (tool):
  1) سابقه تجهیز و MTBF/MTTR را از CMMS (اینجا شبیه‌سازی‌شده) می‌خواند
  2) مقدار سنسور را با آستانه‌های مجاز مقایسه می‌کند
  3) در صورت نیاز، یک Work Order با اولویت مناسب ایجاد می‌کند

این الگو دقیقاً همان معماری ReAct رسمی LangGraph است:
  llm_call -> (تصمیم به tool call) -> tool_node -> برگشت به llm_call -> ... -> END

نیازمندی‌ها:
    pip install langgraph langchain langchain-anthropic python-dotenv --break-system-packages

    کلید API را در یکی از این دو روش تنظیم کن (هرکدام که باشد کافی است):
      1) یک فایل به اسم .env در همان پوشه اسکریپت بساز با محتوای:
             ANTHROPIC_API_KEY=sk-ant-...
         (این روش در Jupyter هم بدون نیاز به Restart کار می‌کند چون پایین
          همین فایل با load_dotenv() خوانده می‌شود)
      2) یا متغیر محیطی سیستم را ست کنی - اما اگر از قبل Jupyter/VS Code باز
         بوده، باید kernel یا ترمینال را Restart کنی تا متغیر جدید دیده شود:
             PowerShell:  $env:ANTHROPIC_API_KEY = "sk-ant-..."
             cmd:         set ANTHROPIC_API_KEY=sk-ant-...

    خطای رایج "Could not resolve authentication method" دقیقاً یعنی هیچ‌کدام
    از این دو راه طی نشده یا کلید به پردازش جاری نرسیده است.
"""

import operator
from typing import Literal
from typing_extensions import TypedDict, Annotated

from dotenv import load_dotenv
from langchain.tools import tool
from langchain.chat_models import init_chat_model
from langchain.messages import AnyMessage, SystemMessage, ToolMessage, HumanMessage
from langgraph.graph import StateGraph, START, END

# فایل .env را (اگر وجود داشته باشد) در متغیرهای محیطی این پردازش بارگذاری می‌کند
load_dotenv()


# ---------------------------------------------------------------------------
# 1) داده شبیه‌سازی‌شده CMMS (در پروژه واقعی این‌جا یک کوئری SQL/FmWeb است)
# ---------------------------------------------------------------------------
CMMS_HISTORY = {
    "P-204": {"mtbf_days": 92, "mttr_hours": 6, "last_failure": "2026-03-11",
              "failure_mode": "seawater seal leak"},
    "C-301": {"mtbf_days": 210, "mttr_hours": 3, "last_failure": "2025-11-02",
              "failure_mode": "bearing wear"},
}

# آستانه‌های مجاز بر اساس نوع پارامتر سنسور (واحد SI)
SENSOR_THRESHOLDS = {
    "temperature_c": 85.0,
    "vibration_mm_s": 4.5,
    "pressure_bar": 12.0,
}


# ---------------------------------------------------------------------------
# 2) ابزارها (Tools) - هر کدام یک قابلیت مجزا برای عامل فراهم می‌کنند
# ---------------------------------------------------------------------------
@tool
def get_equipment_history(equipment_id: str) -> str:
    """سابقه نگهداری یک تجهیز را از CMMS برمی‌گرداند (MTBF، MTTR، آخرین خرابی).

    Args:
        equipment_id: کد تجهیز، مثل P-204 یا C-301
    """
    record = CMMS_HISTORY.get(equipment_id)
    if not record:
        return f"هیچ سابقه‌ای برای تجهیز {equipment_id} ثبت نشده است."
    return (
        f"تجهیز {equipment_id}: MTBF={record['mtbf_days']} روز، "
        f"MTTR={record['mttr_hours']} ساعت، آخرین خرابی در {record['last_failure']} "
        f"به دلیل {record['failure_mode']}."
    )


@tool
def check_sensor_threshold(parameter: str, value: float) -> str:
    """مقدار سنسور را با آستانه ایمن مقایسه می‌کند و وضعیت را برمی‌گرداند.

    Args:
        parameter: یکی از temperature_c, vibration_mm_s, pressure_bar
        value: مقدار اندازه‌گیری‌شده (واحد SI)
    """
    limit = SENSOR_THRESHOLDS.get(parameter)
    if limit is None:
        return f"پارامتر {parameter} تعریف نشده است."
    if value > limit:
        excess_pct = round((value - limit) / limit * 100, 1)
        return f"بحرانی: {parameter}={value} از آستانه {limit} عبور کرده ({excess_pct}% بالاتر)."
    return f"نرمال: {parameter}={value} در محدوده ایمن (آستانه {limit}) است."


@tool
def create_work_order(equipment_id: str, priority: str, description: str) -> str:
    """یک Work Order نگهداری برای تجهیز ثبت می‌کند.

    Args:
        equipment_id: کد تجهیز
        priority: یکی از LOW, MEDIUM, HIGH, URGENT
        description: شرح کار پیشنهادی برای تیم نگهداری
    """
    # در پروژه واقعی اینجا یک POST به API ، CMMS مثل FmWeb قرار می‌گیرد
    work_order_id = f"WO-{equipment_id}-{abs(hash(description)) % 10000}"
    return (
        f"Work Order ثبت شد -> ID={work_order_id}, تجهیز={equipment_id}, "
        f"اولویت={priority}, شرح='{description}'"
    )


tools = [get_equipment_history, check_sensor_threshold, create_work_order]
tools_by_name = {t.name: t for t in tools}

import os

if not os.environ.get("ANTHROPIC_API_KEY"):
    raise RuntimeError(
        "ANTHROPIC_API_KEY ست نشده است. یک فایل .env در همین پوشه با "
        "ANTHROPIC_API_KEY=sk-ant-... بساز، یا متغیر محیطی را تنظیم کن و "
        "kernel/ترمینال را Restart کن."
    )

# مدل Claude را با ابزارها مجهز می‌کنیم
model = init_chat_model("claude-sonnet-4-6", temperature=0)
model_with_tools = model.bind_tools(tools)


# ---------------------------------------------------------------------------
# 3) تعریف State گراف
# ---------------------------------------------------------------------------
class MaintenanceState(TypedDict):
    messages: Annotated[list[AnyMessage], operator.add]
    llm_calls: int


SYSTEM_PROMPT = SystemMessage(content=(
    "تو یک دستیار مهندس نگهداری در یک پتروشیمی هستی. وظیفه تو تریاژ گزارش‌های "
    "خرابی تجهیزات است: ابتدا سابقه تجهیز را بررسی کن، سپس مقدار سنسور را با "
    "آستانه مقایسه کن، و در صورت بحرانی بودن وضعیت یک Work Order با اولویت "
    "مناسب ثبت کن. در پایان یک خلاصه کوتاه برای سرپرست نگهداری بنویس."
))


# ---------------------------------------------------------------------------
# 4) نود LLM - تصمیم می‌گیرد کدام ابزار را صدا بزند یا پاسخ نهایی بدهد
# ---------------------------------------------------------------------------
def llm_call(state: MaintenanceState) -> dict:
    response = model_with_tools.invoke([SYSTEM_PROMPT] + state["messages"])
    return {
        "messages": [response],
        "llm_calls": state.get("llm_calls", 0) + 1,
    }


# ---------------------------------------------------------------------------
# 5) نود اجرای ابزار - tool_call هایی که مدل خواسته را واقعاً اجرا می‌کند
# ---------------------------------------------------------------------------
def tool_node(state: MaintenanceState) -> dict:
    results = []
    for tool_call in state["messages"][-1].tool_calls:
        selected_tool = tools_by_name[tool_call["name"]]
        observation = selected_tool.invoke(tool_call["args"])
        results.append(ToolMessage(content=observation, tool_call_id=tool_call["id"]))
    return {"messages": results}


# ---------------------------------------------------------------------------
# 6) منطق شرطی پایان حلقه
# ---------------------------------------------------------------------------
def should_continue(state: MaintenanceState) -> Literal["tool_node", "__end__"]:
    last_message = state["messages"][-1]
    if last_message.tool_calls:
        return "tool_node"
    return END


# ---------------------------------------------------------------------------
# 7) ساخت و کامپایل گراف
# ---------------------------------------------------------------------------
graph_builder = StateGraph(MaintenanceState)
graph_builder.add_node("llm_call", llm_call)
graph_builder.add_node("tool_node", tool_node)

graph_builder.add_edge(START, "llm_call")
graph_builder.add_conditional_edges("llm_call", should_continue, ["tool_node", END])
graph_builder.add_edge("tool_node", "llm_call")

agent = graph_builder.compile()


# ---------------------------------------------------------------------------
# 8) اجرا - یک گزارش خرابی واقعی را شبیه‌سازی می‌کنیم
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    report = (
        "پمپ P-204 خط آب دریا الان دمای 94 درجه سانتی‌گراد و ویبراسیون 5.2 "
        "میلی‌متر بر ثانیه نشان می‌دهد. لطفاً وضعیت را بررسی و در صورت نیاز اقدام کن."
    )

    final_state = agent.invoke({"messages": [HumanMessage(content=report)]})

    print("\n--- مکالمه کامل عامل ---")
    for m in final_state["messages"]:
        m.pretty_print()

    print(f"\nتعداد فراخوانی مدل (llm_calls): {final_state['llm_calls']}")
