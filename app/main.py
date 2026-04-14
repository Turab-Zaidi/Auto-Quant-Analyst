import streamlit as st
import uuid
import os
import sys
import time
import markdown
from xhtml2pdf import pisa
import io
import base64

# Ensure the src directory is in the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from src.graph.graph_builder import build_graph

# --- PDF GENERATOR UTILITY ---
def generate_pdf(md_text, chart_paths):
    """Converts Markdown text and local images into a PDF byte stream."""
    # 1. Replace image paths in Markdown with Base64 encoded strings so the PDF renderer can see them
    for chart_path in chart_paths:
        local_path = os.path.join("charts", os.path.basename(chart_path))
        if os.path.exists(local_path):
            with open(local_path, "rb") as img_file:
                b64_string = base64.b64encode(img_file.read()).decode('utf-8')
                img_uri = f"data:image/png;base64,{b64_string}"
                md_text = md_text.replace(chart_path, img_uri)
                
    # 2. Convert Markdown to HTML
    html_text = markdown.markdown(md_text, extensions=['tables'])
    
    # 3. Add Professional CSS Styling
    full_html = f"""
    <html><head><style>
        @page {{ margin: 2cm; }}
        body {{ font-family: Helvetica, Arial, sans-serif; color: #333; line-height: 1.6; font-size: 12px; }}
        h1 {{ color: #2C3E50; border-bottom: 2px solid #34495E; padding-bottom: 5px; margin-top: 30px; }}
        h2 {{ color: #34495E; margin-top: 20px; }}
        p {{ margin-bottom: 10px; }}
        li {{ margin-bottom: 6px; }}
        img {{ max-width: 100%; height: auto; margin-top: 20px; margin-bottom: 20px; }}
    </style></head><body>
    {html_text}
    </body></html>
    """
    
    # 4. Generate PDF
    result_file = io.BytesIO()
    pisa_status = pisa.CreatePDF(io.StringIO(full_html), dest=result_file)
    
    if pisa_status.err:
        return None
    return result_file.getvalue()


# --- 1. PAGE CONFIGURATION ---
st.set_page_config(page_title="Auto-Quant Terminal", page_icon="🏦", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
<style>
    .stMetric { background-color: #1E2130; padding: 15px; border-radius: 5px; border-left: 5px solid #4CAF50; }
    .stMetric-Risk { border-left: 5px solid #FF5252 !important; }
    .stMetric-Sentiment { border-left: 5px solid #2196F3 !important; }
    .stMetric-Confidence { border-left: 5px solid #FFC107 !important; }
    h1, h2, h3 { color: #FFFFFF !important; }
</style>
""", unsafe_allow_html=True)

st.title("🏦 Auto-Quant Intelligence Terminal")
st.markdown("`SYSTEM STATUS: ONLINE` | `MODE: ENTERPRISE MULTI-AGENT`")
st.markdown("---")

# --- 2. INITIALIZE SESSION STATE ---
if "graph" not in st.session_state:
    st.session_state.graph = build_graph()
if "thread_id" not in st.session_state:
    st.session_state.thread_id = str(uuid.uuid4())
if "phase" not in st.session_state:
    st.session_state.phase = "INPUT" 
if "final_report" not in st.session_state:
    st.session_state.final_report = None
if "charts" not in st.session_state:
    st.session_state.charts = []

config = {"configurable": {"thread_id": st.session_state.thread_id}}

# --- 3. SIDEBAR: COMMAND CENTER ---
with st.sidebar:
    st.image("https://upload.wikimedia.org/wikipedia/commons/thumb/8/82/S%26P_500_Logo.svg/512px-S%26P_500_Logo.svg.png", width=150)
    st.header("Command Center")
    user_query = st.text_area("Enter Target & Parameters:", placeholder="e.g., Give me an in-depth analysis of Amazon.")
    start_button = st.button("⚡ EXECUTE PIPELINE", type="primary", use_container_width=True)
    
    if start_button and user_query:
        st.session_state.thread_id = str(uuid.uuid4())
        st.session_state.phase = "RUNNING"
        st.session_state.final_report = None
        st.session_state.charts = []
        st.rerun()

# --- 4. MAIN PANEL: LIVE EXECUTION (CENTER SCREEN) ---
if st.session_state.phase == "RUNNING":
    initial_state = {"raw_query": user_query, "supervisor_iteration_count": 0, "synthesis_iteration_count": 0}
    config = {"configurable": {"thread_id": st.session_state.thread_id}}
    
    st.markdown("### ⚙️ Live System Execution Logs")
    
    # The Live Terminal in the center of the screen
    with st.status("🟢 Initializing Auto-Quant Engine...", expanded=True) as status:
        st.write("`[SYS]` Connecting to LangGraph Orchestrator...")
        
        for event in st.session_state.graph.stream(initial_state, config, stream_mode="updates"):
            for node_name, node_state in event.items():
                agent_name = node_name.replace("_", " ").title()
                
                # Detailed Center-Console Logging
                if node_name == "intake_agent":
                    req = node_state.get("analysis_request")
                    st.write(f"🎯 `[{agent_name}]` Target Acquired: **{req.ticker if req else 'Unknown'}**.")
                    
                elif node_name == "synthesis_agent":
                    st.write(f"🧠 `[{agent_name}]` Synthesis drafted and critiqued.")
                    re_req = node_state.get("re_research_request")
                    if re_req:
                        st.warning(f"🔄 **SELF-HEALING TRIGGERED!**")
                        st.write(f"> **Action:** Re-routing to `{re_req.target_agent}` for deeper analysis.")
                        st.write(f"> **AI Rationale:** _{re_req.reason}_")
                else:
                    st.write(f"✅ `[{agent_name}]` completed task.")
                    
        status.update(label="⏸️ Pipeline Reached Checkpoint", state="complete", expanded=False)
    
    st.session_state.phase = "HITL"
    st.rerun()

# --- 5. MAIN PANEL: HITL CHECKPOINT ---
if st.session_state.phase == "HITL":
    config = {"configurable": {"thread_id": st.session_state.thread_id}}
    current_state = st.session_state.graph.get_state(config)
    
    if "report_compiler" in current_state.next:
        st.warning("⚠️ **ACTION REQUIRED: PORTFOLIO MANAGER REVIEW**")
        
        with st.container(border=True):
            st.subheader("Draft Intelligence Report")
            
            confidence = current_state.values.get("synthesis_confidence_score", "N/A")
            synthesis = current_state.values.get("synthesis_final", "Error generating synthesis.")
            risk_report = current_state.values.get("risk_report")
            iterations = current_state.values.get("synthesis_iteration_count", 1)

            if iterations > 1:
                st.info(f"🔄 **Self-Healing Complete:** The AI performed {iterations-1} extra research loop(s) to resolve contradictions before presenting this draft.")

            col1, col2, col3 = st.columns(3)
            col1.metric("Final AI Confidence", f"{confidence}/100")
            col2.metric("Research Iterations", iterations)
            col3.metric("Data Freshness", "Live")
            
            st.markdown("### Executive Thesis Draft")
            st.info(synthesis)

            if risk_report:
                st.markdown("### Primary Risk Contradiction")
                st.warning(risk_report.primary_contradiction)

            col_approve, col_abort = st.columns(2)
            with col_approve:
                if st.button("✅ Approve & Publish Final Report", use_container_width=True, type="primary"):
                    st.session_state.phase = "COMPILING"
                    st.rerun()
            with col_abort:
                if st.button("❌ Reject & Abort", use_container_width=True):
                    st.session_state.phase = "INPUT"
                    st.error("Pipeline Terminated by User.")
                    time.sleep(1.5)
                    st.rerun()
    else:
        st.session_state.phase = "COMPLETE"
        st.rerun()

# --- 6. MAIN PANEL: COMPILING FINAL REPORT ---
if st.session_state.phase == "COMPILING":
    config = {"configurable": {"thread_id": st.session_state.thread_id}}
    
    with st.status("🖨️ Compiling Final Markdown Report...", expanded=True) as status:
        for event in st.session_state.graph.stream(None, config, stream_mode="updates"):
            for node_name, _ in event.items():
                st.write(f"✅ `[{node_name}]` complete.")
        status.update(label="✅ Report Published", state="complete")
        
    final_state = st.session_state.graph.get_state(config).values
    st.session_state.final_report = final_state.get('final_report_markdown')
    st.session_state.charts = final_state.get('chart_file_paths', [])
    
    fund_report = final_state.get("fundamental_report")
    sent_report = final_state.get("sentiment_report")
    risk_report = final_state.get("risk_report")
    
    st.session_state.kpis = {
        "conf": final_state.get("synthesis_confidence_score", "N/A"),
        "fund_score": fund_report.fundamental_score if fund_report else "N/A",
        "sentiment": sent_report.overall_sentiment if sent_report else "N/A",
        "risk": risk_report.overall_risk_level if risk_report else "N/A",
        "ticker": final_state.get("analysis_request").ticker if final_state.get("analysis_request") else "Report"
    }
    
    st.session_state.phase = "COMPLETE"
    st.rerun()

# --- 7. MAIN PANEL: FINAL REPORT DISPLAY ---
if st.session_state.phase == "COMPLETE" and st.session_state.final_report:
    st.success("✅ Intelligence Pipeline Execution Complete.")
    
    st.markdown("### 📊 Top-Level Metrics")
    kpi1, kpi2, kpi3, kpi4 = st.columns(4)
    kpis = st.session_state.get("kpis", {})
    
    kpi1.markdown(f"<div class='stMetric stMetric-Confidence'><p style='margin:0;color:#888;'>AI Confidence</p><h2 style='margin:0;'>{kpis.get('conf')}/100</h2></div>", unsafe_allow_html=True)
    kpi2.markdown(f"<div class='stMetric'><p style='margin:0;color:#888;'>Fundamental Score</p><h2 style='margin:0;'>{kpis.get('fund_score')}/100</h2></div>", unsafe_allow_html=True)
    kpi3.markdown(f"<div class='stMetric stMetric-Sentiment'><p style='margin:0;color:#888;'>Market Sentiment</p><h2 style='margin:0;'>{kpis.get('sentiment')}</h2></div>", unsafe_allow_html=True)
    kpi4.markdown(f"<div class='stMetric stMetric-Risk'><p style='margin:0;color:#888;'>Risk Assessment</p><h2 style='margin:0;'>{kpis.get('risk')}</h2></div>", unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Tab 3 is now Download PDF!
    tab1, tab2, tab3 = st.tabs(["📄 Investment Memo", "📊 Technical Dashboard", "📥 Export Options"])
    
    with tab1:
        report_content = st.session_state.final_report
        if "![Technical Dashboard]" in report_content:
            parts = report_content.split("![Technical Dashboard]")
            st.markdown(parts[0])
            
            if st.session_state.charts:
                for chart_path in st.session_state.charts:
                    local_path = os.path.join("charts", os.path.basename(chart_path))
                    if os.path.exists(local_path):
                        st.image(local_path, use_container_width=True)
            
            if len(parts) > 1:
                remaining_text = parts[1].split(")", 1)[-1] if ")" in parts[1] else parts[1]
                st.markdown(remaining_text)
        else:
            st.markdown(report_content)
        
    with tab2:
        if st.session_state.charts:
            for chart_path in st.session_state.charts:
                local_path = os.path.join("charts", os.path.basename(chart_path))
                if os.path.exists(local_path):
                    st.image(local_path, use_container_width=True)
        else:
            st.info("No charts generated.")
            
    with tab3:
        st.markdown("### Export Full Report to PDF")
        st.write("Generate a formatted PDF document containing the full narrative investment memo and all technical charts.")
        
        # When user clicks, generate PDF byte stream on the fly
        if st.button("Generate PDF Document", type="primary"):
            with st.spinner("Rendering PDF..."):
                pdf_bytes = generate_pdf(st.session_state.final_report, st.session_state.charts)
                
            if pdf_bytes:
                st.success("PDF generated successfully!")
                file_name = f"{kpis.get('ticker')}_Investment_Memo.pdf"
                
                # Show the native Streamlit download button
                st.download_button(
                    label=f"⬇️ Download {file_name}",
                    data=pdf_bytes,
                    file_name=file_name,
                    mime="application/pdf",
                    type="primary"
                )
            else:
                st.error("Failed to generate PDF. Check terminal logs.")