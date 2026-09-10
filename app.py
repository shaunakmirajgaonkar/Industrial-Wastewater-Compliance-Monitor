import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path

st.set_page_config(page_title="Industrial Wastewater Compliance Monitor", page_icon="💧", layout="wide")

# ---------- Professional light UI ----------
st.markdown("""
<style>
.stApp{background:linear-gradient(135deg,#f5fbff 0%,#eef8f6 52%,#fbf8ff 100%);color:#173047}
.block-container{max-width:1580px;padding-top:1rem}
[data-testid="stSidebar"]{background:linear-gradient(180deg,#eaf8f7,#f7fbff);border-right:1px solid #d5e7e8}
[data-testid="stSidebar"] *{color:#183246}
.hero{background:linear-gradient(120deg,#075985,#087f8c 52%,#5366b7);border-radius:28px;padding:30px;color:white;box-shadow:0 16px 40px #07598520;margin-bottom:18px}
.hero h1{color:white!important;font-size:2.35rem;margin:0;letter-spacing:-.8px}
.hero p{color:#e9fbff;margin:7px 0 0;font-size:1rem}
.pill{display:inline-block;background:#ffffff22;border:1px solid #ffffff3a;border-radius:99px;padding:5px 12px;font-size:.69rem;font-weight:800;letter-spacing:.5px}
.card{background:#fff;border:1px solid #d9e8ea;border-radius:20px;padding:18px;box-shadow:0 8px 28px #1c536010;margin-bottom:16px}
.cardtitle{font-weight:800;font-size:1.12rem;color:#173d55}
.muted{color:#6a8192;font-size:.82rem}
.alert{background:#fff0f0;border-left:4px solid #dc3f52;border-radius:11px;padding:11px 13px;margin:7px 0}
.warn{background:#fff8e9;border-left:4px solid #e49b16;border-radius:11px;padding:11px 13px;margin:7px 0}
.good{background:#effbf5;border-left:4px solid #15966b;border-radius:11px;padding:11px 13px;margin:7px 0}
.info{background:#eef8ff;border-left:4px solid #1284bb;border-radius:11px;padding:11px 13px;margin:7px 0}
.stButton>button{border-radius:11px;font-weight:750}
div[data-testid="stMetric"]{background:#fff;border:1px solid #d9e8ea;border-radius:16px;padding:10px}
.footer{text-align:center;color:#7890a0;font-size:.75rem;padding:16px}
.section{font-size:1.35rem;font-weight:850;color:#16455f;margin:5px 0 12px}
</style>
""", unsafe_allow_html=True)

DATA = Path(__file__).parent / "data" / "sample_wastewater_compliance_records.csv"

LIMITS = {
    "pH": (6.0, 9.0),
    "COD_mg_L": (0, 250),
    "BOD_mg_L": (0, 100),
    "TSS_mg_L": (0, 100),
    "ammonia_mg_L": (0, 30),
    "nitrate_mg_L": (0, 45),
    "phosphate_mg_L": (0, 10),
    "oil_grease_mg_L": (0, 10),
    "temperature_c": (0, 40),
}

@st.cache_data
def load_data():
    return pd.read_csv(DATA)

def exceedance(value, low, high):
    if low <= value <= high:
        return 0.0
    if value < low:
        return min(100.0, (low-value)/max(abs(low),1)*100)
    return min(100.0, (value-high)/max(abs(high),1)*100)

def assess(r):
    # Explainable screening heuristic, not a regulatory determination.
    factors = {}
    for col,(lo,hi) in LIMITS.items():
        factors[col] = exceedance(float(r[col]),lo,hi)

    flow = min(100, float(r.flow_m3_day)/10000*100)
    treatment = np.clip((100-float(r.treatment_efficiency_pct)),0,100)
    weather = {"Heavy Rain":80,"Moderate Rain":45,"Dry":10,"Storm":95,"Snowmelt":60}.get(str(r.weather_condition),25)
    inspection = {"Failed":90,"Overdue":70,"Needs Follow-up":55,"Passed":10}.get(str(r.inspection_status),40)
    corrective = {"Open":75,"In Progress":45,"Closed":5}.get(str(r.corrective_action_status),40)
    age = min(100,float(r.days_since_inspection)/180*100)
    discharge = min(100,float(r.discharge_duration_h)/24*100)

    # Convert chemistry deviations into a combined signal.
    chemistry = float(np.mean(list(factors.values())))
    components = {
        "Chemical exceedance": chemistry,
        "Flow intensity": flow,
        "Treatment performance gap": treatment,
        "Weather / dilution signal": weather,
        "Inspection status": inspection,
        "Corrective-action status": corrective,
        "Inspection age": age,
        "Discharge duration": discharge,
    }
    weights = [0.34,0.08,0.16,0.08,0.12,0.10,0.06,0.06]
    risk = float(np.clip(sum(v*w for v,w in zip(components.values(),weights)),0,100))

    violations = [k for k,v in factors.items() if v>0]
    if risk >= 72:
        band, action = "CRITICAL", "IMMEDIATE REVIEW"
    elif risk >= 55:
        band, action = "HIGH", "PRIORITY REVIEW"
    elif risk >= 35:
        band, action = "MODERATE", "MONITOR / FOLLOW UP"
    else:
        band, action = "LOW", "ROUTINE MONITORING"

    return risk,100-risk,band,action,violations,components

df = load_data()
out = df.apply(assess,axis=1,result_type="expand")
out.columns=["risk_score","control_score","risk_band","recommended_action","violations","components"]
df = pd.concat([df,out],axis=1)

# ---------- Sidebar ----------
with st.sidebar:
    st.markdown("## 💧 AquaGuard")
    st.caption("WASTEWATER COMPLIANCE INTELLIGENCE")
    page = st.radio("MAIN NAVIGATION",[
        "🏠 Command Center",
        "🧪 Discharge Assessment",
        "⚗️ Chemical Compliance",
        "💦 Flow & Load Monitor",
        "⚙️ Treatment Performance",
        "🌦️ Weather Impact",
        "🔍 Inspection Intelligence",
        "🚨 Compliance Control Tower",
        "🏭 Facility Intelligence",
        "📊 Parameter Analytics",
        "📅 Compliance Timeline",
        "🧮 What-If Simulator",
        "🔔 Alert Center",
        "📂 Data Operations",
        "⚙️ Methodology & System"
    ])
    st.divider()
    risk_threshold=st.slider("Priority-review threshold",40,90,55)
    critical_threshold=st.slider("Critical threshold",55,95,72)
    st.divider()
    st.caption("100% LOCAL PROCESSING")
    st.write("Pandas • NumPy • Plotly")
    st.write(f"Records: **{len(df)}**")
    st.write(f"Facilities: **{df.facility_name.nunique()}**")
    st.caption("No external APIs required.")

st.markdown("""<div class="hero"><span class="pill">ADVANCED • LOCAL-FIRST • ENVIRONMENTAL GOVERNANCE</span>
<h1>💧 Industrial Wastewater Compliance Monitor</h1>
<p>Explainable screening of possible discharge-compliance issues using flow, chemical readings, treatment performance, weather and inspection signals.</p></div>""",unsafe_allow_html=True)

def kpis(data):
    c=st.columns(5)
    c[0].metric("Records screened",len(data))
    c[1].metric("Average risk",f"{data.risk_score.mean():.1f}/100")
    c[2].metric("Priority review",f"{(data.risk_score>=risk_threshold).mean()*100:.0f}%")
    c[3].metric("Critical records",int((data.risk_score>=critical_threshold).sum()))
    c[4].metric("Parameter alerts",int(data.violations.apply(len).sum()))

# ---------- Command Center ----------
if page=="🏠 Command Center":
    kpis(df)
    a,b=st.columns([1.45,1])
    with a:
        st.markdown('<div class="card"><div class="cardtitle">Compliance Risk Landscape</div><div class="muted">Chemical intensity versus treatment performance.</div>',unsafe_allow_html=True)
        fig=px.scatter(df,x="treatment_efficiency_pct",y="risk_score",size="flow_m3_day",color="risk_score",
                       hover_name="record_id",hover_data=["facility_name","discharge_point","weather_condition"],
                       color_continuous_scale=["#16a34a","#0891b2","#f59e0b","#dc2626"])
        fig.update_layout(height=430,margin=dict(l=5,r=5,t=10,b=5))
        st.plotly_chart(fig,use_container_width=True)
        st.markdown("</div>",unsafe_allow_html=True)
    with b:
        st.markdown('<div class="card"><div class="cardtitle">Risk Portfolio</div><div class="muted">Current screening classification.</div>',unsafe_allow_html=True)
        x=df.risk_band.value_counts().reindex(["LOW","MODERATE","HIGH","CRITICAL"]).fillna(0)
        fig=px.pie(values=x.values,names=x.index,hole=.58,color=x.index,
                   color_discrete_map={"LOW":"#16a34a","MODERATE":"#0891b2","HIGH":"#f59e0b","CRITICAL":"#dc2626"})
        fig.update_layout(height=430,margin=dict(l=0,r=0,t=5,b=0))
        st.plotly_chart(fig,use_container_width=True)
        st.markdown("</div>",unsafe_allow_html=True)
    a,b=st.columns(2)
    with a:
        st.markdown('<div class="card"><div class="cardtitle">Facility Scorecard</div>',unsafe_allow_html=True)
        g=df.groupby("facility_name").agg(Risk=("risk_score","mean"),Control=("control_score","mean"),Records=("record_id","size")).reset_index()
        st.dataframe(g.style.format({"Risk":"{:.1f}","Control":"{:.1f}"}),use_container_width=True,hide_index=True)
        st.markdown("</div>",unsafe_allow_html=True)
    with b:
        st.markdown('<div class="card"><div class="cardtitle">Priority Queue</div>',unsafe_allow_html=True)
        for _,r in df.nlargest(6,"risk_score").iterrows():
            cls="alert" if r.risk_score>=critical_threshold else "warn"
            st.markdown(f'<div class="{cls}"><b>{r.record_id}</b> · {r.facility_name}<br>Risk <b>{r.risk_score:.0f}/100</b> · {r.recommended_action}</div>',unsafe_allow_html=True)
        st.markdown("</div>",unsafe_allow_html=True)

# ---------- Discharge Assessment ----------
elif page=="🧪 Discharge Assessment":
    st.markdown('<div class="card"><div class="cardtitle">🧪 Advanced Discharge Assessment</div><div class="muted">Enter locally measured discharge conditions for an explainable screening assessment.</div></div>',unsafe_allow_html=True)
    with st.form("assessment"):
        a,b,c=st.columns(3)
        with a:
            rid=st.text_input("Record ID","NEW-WW-01");facility=st.text_input("Facility","New Industrial Facility")
            point=st.text_input("Discharge point","OUT-01");date=st.date_input("Record date")
            flow=st.number_input("Flow (m³/day)",0.,50000.,4500.,100.)
            duration=st.number_input("Discharge duration (hours)",0.,48.,12.,.5)
        with b:
            ph=st.number_input("pH",0.,14.,7.2,.1);cod=st.number_input("COD (mg/L)",0.,1000.,180.,5.)
            bod=st.number_input("BOD (mg/L)",0.,500.,55.,5.);tss=st.number_input("TSS (mg/L)",0.,500.,70.,5.)
            ammonia=st.number_input("Ammonia (mg/L)",0.,200.,18.,1.)
        with c:
            nitrate=st.number_input("Nitrate (mg/L)",0.,200.,25.,1.);phosphate=st.number_input("Phosphate (mg/L)",0.,100.,6.,.5)
            oil=st.number_input("Oil & grease (mg/L)",0.,100.,6.,.5);temp=st.number_input("Temperature (°C)",0.,80.,29.,.5)
            eff=st.number_input("Treatment efficiency (%)",0.,100.,88.,1.)
        d,e,f=st.columns(3)
        with d: weather=st.selectbox("Weather",["Dry","Moderate Rain","Heavy Rain","Storm","Snowmelt"])
        with e: inspection=st.selectbox("Inspection status",["Passed","Needs Follow-up","Overdue","Failed"])
        with f: corrective=st.selectbox("Corrective action",["Closed","In Progress","Open"])
        days=st.number_input("Days since inspection",0,1000,45,1)
        run=st.form_submit_button("RUN COMPLIANCE SCREEN",use_container_width=True)
    if run:
        r=pd.Series(dict(record_id=rid,facility_name=facility,discharge_point=point,date=str(date),flow_m3_day=flow,
                         discharge_duration_h=duration,pH=ph,COD_mg_L=cod,BOD_mg_L=bod,TSS_mg_L=tss,
                         ammonia_mg_L=ammonia,nitrate_mg_L=nitrate,phosphate_mg_L=phosphate,oil_grease_mg_L=oil,
                         temperature_c=temp,treatment_efficiency_pct=eff,weather_condition=weather,
                         inspection_status=inspection,corrective_action_status=corrective,days_since_inspection=days))
        risk,control,band,action,violations,components=assess(r)
        z=st.columns(5)
        z[0].metric("Risk",f"{risk:.0f}/100");z[1].metric("Control",f"{control:.0f}/100");z[2].metric("Band",band);z[3].metric("Action",action);z[4].metric("Parameter alerts",len(violations))
        cls="alert" if risk>=critical_threshold else "warn" if risk>=risk_threshold else "good"
        st.markdown(f'<div class="{cls}"><b>{action}</b> — screening risk {risk:.0f}/100. This does not establish regulatory non-compliance.</div>',unsafe_allow_html=True)
        if violations: st.warning("Potential parameter-limit signals: "+", ".join(violations))
        else: st.success("No configured parameter-limit signal detected.")
        fd=pd.DataFrame({"Factor":list(components),"Signal":list(components.values())}).sort_values("Signal")
        fig=px.bar(fd,x="Signal",y="Factor",orientation="h",color="Signal",color_continuous_scale=["#16a34a","#0891b2","#f59e0b","#dc2626"],range_x=[0,100])
        fig.update_layout(height=410);st.plotly_chart(fig,use_container_width=True)

# ---------- Chemical ----------
elif page=="⚗️ Chemical Compliance":
    st.markdown('<div class="card"><div class="cardtitle">⚗️ Chemical Compliance Matrix</div><div class="muted">Compare locally supplied readings with configurable screening reference ranges.</div></div>',unsafe_allow_html=True)
    params=list(LIMITS)
    vals=[]
    for p in params:
        vals.append([p,LIMITS[p][0],LIMITS[p][1],df[p].mean(),int((df[p].apply(lambda x: exceedance(x,*LIMITS[p]))>0).sum())])
    t=pd.DataFrame(vals,columns=["Parameter","Lower reference","Upper reference","Average","Records flagged"])
    st.dataframe(t,use_container_width=True,hide_index=True)
    sel=st.selectbox("Parameter",params)
    fig=px.histogram(df,x=sel,color="risk_band",nbins=18,color_discrete_map={"LOW":"#16a34a","MODERATE":"#0891b2","HIGH":"#f59e0b","CRITICAL":"#dc2626"})
    fig.add_vline(x=LIMITS[sel][1],line_dash="dash");fig.add_vline(x=LIMITS[sel][0],line_dash="dash")
    fig.update_layout(height=410);st.plotly_chart(fig,use_container_width=True)

# ---------- Flow ----------
elif page=="💦 Flow & Load Monitor":
    st.markdown('<div class="card"><div class="cardtitle">💦 Flow & Discharge Load Monitor</div><div class="muted">Screen discharge intensity, duration and risk exposure.</div></div>',unsafe_allow_html=True)
    a,b,c=st.columns(3);a.metric("Average flow",f"{df.flow_m3_day.mean():,.0f} m³/day");b.metric("High-flow records",int((df.flow_m3_day>8000).sum()));c.metric("Avg duration",f"{df.discharge_duration_h.mean():.1f} h")
    fig=px.scatter(df,x="flow_m3_day",y="discharge_duration_h",size="COD_mg_L",color="risk_score",hover_name="record_id",color_continuous_scale=["#16a34a","#f59e0b","#dc2626"])
    fig.update_layout(height=430);st.plotly_chart(fig,use_container_width=True)
    st.dataframe(df[["record_id","facility_name","flow_m3_day","discharge_duration_h","COD_mg_L","BOD_mg_L","risk_score","risk_band"]].sort_values("flow_m3_day",ascending=False),use_container_width=True,hide_index=True)

# ---------- Treatment ----------
elif page=="⚙️ Treatment Performance":
    st.markdown('<div class="card"><div class="cardtitle">⚙️ Treatment Performance</div><div class="muted">Identify records where lower treatment performance coincides with elevated risk.</div></div>',unsafe_allow_html=True)
    fig=px.scatter(df,x="treatment_efficiency_pct",y="risk_score",size="flow_m3_day",color="facility_name",hover_name="record_id")
    fig.add_vline(x=90,line_dash="dash");fig.update_layout(height=430);st.plotly_chart(fig,use_container_width=True)
    g=df.groupby("facility_name").agg(Avg_Efficiency=("treatment_efficiency_pct","mean"),Avg_Risk=("risk_score","mean"),Records=("record_id","size")).reset_index()
    st.dataframe(g.style.format({"Avg_Efficiency":"{:.1f}","Avg_Risk":"{:.1f}"}),use_container_width=True,hide_index=True)

# ---------- Weather ----------
elif page=="🌦️ Weather Impact":
    st.markdown('<div class="card"><div class="cardtitle">🌦️ Weather Impact Monitor</div><div class="muted">Compare weather context with discharge and compliance screening signals.</div></div>',unsafe_allow_html=True)
    g=df.groupby("weather_condition").agg(Risk=("risk_score","mean"),Flow=("flow_m3_day","mean"),Records=("record_id","size")).reset_index()
    fig=px.bar(g,x="weather_condition",y="Risk",color="Risk",color_continuous_scale=["#16a34a","#f59e0b","#dc2626"],range_y=[0,100])
    fig.update_layout(height=390);st.plotly_chart(fig,use_container_width=True)
    st.dataframe(g.style.format({"Risk":"{:.1f}","Flow":"{:.0f}"}),use_container_width=True,hide_index=True)

# ---------- Inspections ----------
elif page=="🔍 Inspection Intelligence":
    st.markdown('<div class="card"><div class="cardtitle">🔍 Inspection Intelligence</div><div class="muted">Track inspection recency, outcomes and open corrective actions.</div></div>',unsafe_allow_html=True)
    a,b,c=st.columns(3);a.metric("Overdue / failed",int(df.inspection_status.isin(["Overdue","Failed"]).sum()));b.metric("Open corrective actions",int((df.corrective_action_status=="Open").sum()));c.metric("Avg days since inspection",f"{df.days_since_inspection.mean():.0f}")
    fig=px.scatter(df,x="days_since_inspection",y="risk_score",color="inspection_status",size="flow_m3_day",hover_name="record_id",
                   color_discrete_map={"Passed":"#16a34a","Needs Follow-up":"#0891b2","Overdue":"#f59e0b","Failed":"#dc2626"})
    fig.update_layout(height=420);st.plotly_chart(fig,use_container_width=True)
    st.dataframe(df[["record_id","facility_name","date","inspection_status","days_since_inspection","corrective_action_status","risk_score","risk_band"]].sort_values("days_since_inspection",ascending=False),use_container_width=True,hide_index=True)

# ---------- Control tower ----------
elif page=="🚨 Compliance Control Tower":
    st.markdown('<div class="card"><div class="cardtitle">🚨 Compliance Control Tower</div><div class="muted">Prioritise records for human review using risk, flow exposure and governance status.</div></div>',unsafe_allow_html=True)
    x=df.copy()
    x["priority_score"]=x.risk_score*.70+np.clip(x.flow_m3_day/10000*100,0,100)*.12+np.clip(x.days_since_inspection/180*100,0,100)*.10+np.where(x.corrective_action_status=="Open",100,20)*.08
    x=x.sort_values("priority_score",ascending=False)
    fig=px.bar(x.head(12),x="priority_score",y="record_id",orientation="h",color="risk_band",
               color_discrete_map={"LOW":"#16a34a","MODERATE":"#0891b2","HIGH":"#f59e0b","CRITICAL":"#dc2626"})
    fig.update_layout(height=470);st.plotly_chart(fig,use_container_width=True)
    st.dataframe(x[["record_id","facility_name","risk_score","flow_m3_day","days_since_inspection","corrective_action_status","priority_score","recommended_action"]].head(20),use_container_width=True,hide_index=True)

# ---------- Facility ----------
elif page=="🏭 Facility Intelligence":
    st.markdown('<div class="card"><div class="cardtitle">🏭 Facility Intelligence</div><div class="muted">Compare facility-level risk, treatment performance and parameter signals.</div></div>',unsafe_allow_html=True)
    g=df.groupby("facility_name").agg(Risk=("risk_score","mean"),Treatment=("treatment_efficiency_pct","mean"),Flow=("flow_m3_day","mean"),Records=("record_id","size")).reset_index()
    fig=px.scatter(g,x="Treatment",y="Risk",size="Flow",hover_name="facility_name",color="Risk",color_continuous_scale=["#16a34a","#f59e0b","#dc2626"],range_y=[0,100])
    fig.update_layout(height=420);st.plotly_chart(fig,use_container_width=True)
    st.dataframe(g.style.format({"Risk":"{:.1f}","Treatment":"{:.1f}","Flow":"{:.0f}"}),use_container_width=True,hide_index=True)

# ---------- Parameter analytics ----------
elif page=="📊 Parameter Analytics":
    st.markdown('<div class="card"><div class="cardtitle">📊 Parameter Analytics</div><div class="muted">Explore distributions and relationship with screening risk.</div></div>',unsafe_allow_html=True)
    sel=st.selectbox("Select parameter",list(LIMITS),index=1)
    fig=px.scatter(df,x=sel,y="risk_score",color="facility_name",size="flow_m3_day",hover_name="record_id")
    fig.update_layout(height=430);st.plotly_chart(fig,use_container_width=True)
    st.dataframe(df[["record_id","facility_name","date",sel,"risk_score","risk_band"]].sort_values("risk_score",ascending=False),use_container_width=True,hide_index=True)

# ---------- Timeline ----------
elif page=="📅 Compliance Timeline":
    st.markdown('<div class="card"><div class="cardtitle">📅 Compliance Timeline</div><div class="muted">Daily screening risk and inspection activity from supplied records.</div></div>',unsafe_allow_html=True)
    x=df.copy();x["date"]=pd.to_datetime(x.date)
    d=x.groupby("date").agg(Risk=("risk_score","mean"),Flow=("flow_m3_day","mean"),Records=("record_id","size")).reset_index()
    fig=px.line(d,x="date",y=["Risk","Flow"],markers=True);fig.update_layout(height=420);st.plotly_chart(fig,use_container_width=True)
    st.dataframe(d.style.format({"Risk":"{:.1f}","Flow":"{:.0f}"}),use_container_width=True,hide_index=True)

# ---------- What-if ----------
elif page=="🧮 What-If Simulator":
    st.markdown('<div class="card"><div class="cardtitle">🧮 What-If Compliance Simulator</div><div class="muted">Test how operational changes could alter the screening score.</div></div>',unsafe_allow_html=True)
    rid=st.selectbox("Select record",df.record_id.tolist());base=df[df.record_id==rid].iloc[0];base_risk=assess(base)[0]
    a,b=st.columns(2)
    with a:
        cod=st.slider("Scenario COD (mg/L)",0.,1000.,float(base.COD_mg_L),5.);flow=st.slider("Scenario flow (m³/day)",0.,50000.,float(base.flow_m3_day),100.)
        eff=st.slider("Scenario treatment efficiency (%)",0.,100.,float(base.treatment_efficiency_pct),1.)
    with b:
        r=base.copy();r["COD_mg_L"]=cod;r["flow_m3_day"]=flow;r["treatment_efficiency_pct"]=eff
        new=assess(r)[0];st.metric("Baseline risk",f"{base_risk:.0f}/100");st.metric("Scenario risk",f"{new:.0f}/100",f"{new-base_risk:+.0f}");st.metric("Risk change",f"{new-base_risk:+.0f} points")
    fig=go.Figure(go.Indicator(mode="gauge+number",value=new,title={"text":"Scenario risk"},gauge={"axis":{"range":[0,100]},"bar":{"color":"#087f8c"}}));fig.update_layout(height=300);st.plotly_chart(fig,use_container_width=True)

# ---------- Alerts ----------
elif page=="🔔 Alert Center":
    st.markdown('<div class="card"><div class="cardtitle">🔔 Alert Center</div><div class="muted">Local rule-based alerts generated from the supplied records.</div></div>',unsafe_allow_html=True)
    alerts=[]
    for _,r in df.iterrows():
        if r.risk_score>=critical_threshold: alerts.append((r.record_id,"CRITICAL","Composite screening risk exceeds critical threshold."))
        if len(r.violations)>0: alerts.append((r.record_id,"PARAMETER","One or more configured reference limits are exceeded."))
        if r.inspection_status in ["Overdue","Failed"]: alerts.append((r.record_id,"INSPECTION",f"Inspection status: {r.inspection_status}."))
        if r.corrective_action_status=="Open": alerts.append((r.record_id,"ACTION","Corrective action remains open."))
        if r.weather_condition in ["Heavy Rain","Storm"]: alerts.append((r.record_id,"WEATHER",f"Weather signal: {r.weather_condition}."))
    for rid,typ,msg in alerts:
        cls="alert" if typ=="CRITICAL" else "warn"
        st.markdown(f'<div class="{cls}"><b>{rid} · {typ}</b> — {msg}</div>',unsafe_allow_html=True)
    if not alerts: st.success("No rule-based alerts.")

# ---------- Data ----------
elif page=="📂 Data Operations":
    st.markdown('<div class="card"><div class="cardtitle">📂 Data Operations</div><div class="muted">Upload, validate, screen and export local wastewater records.</div></div>',unsafe_allow_html=True)
    up=st.file_uploader("Upload CSV",type=["csv"]);work=df.copy()
    required=["record_id","facility_name","discharge_point","date","flow_m3_day","discharge_duration_h","pH","COD_mg_L","BOD_mg_L","TSS_mg_L","ammonia_mg_L","nitrate_mg_L","phosphate_mg_L","oil_grease_mg_L","temperature_c","treatment_efficiency_pct","weather_condition","inspection_status","corrective_action_status","days_since_inspection"]
    if up:
        raw=pd.read_csv(up);missing=[c for c in required if c not in raw.columns]
        if missing: st.error("Missing columns: "+", ".join(missing))
        else:
            z=raw.apply(assess,axis=1,result_type="expand");z.columns=["risk_score","control_score","risk_band","recommended_action","violations","components"]
            work=pd.concat([raw,z],axis=1);st.success(f"Validated and screened {len(work)} records locally.")
    f1,f2=st.columns(2)
    with f1: facilities=st.multiselect("Facility",sorted(work.facility_name.unique()))
    with f2: bands=st.multiselect("Risk band",["LOW","MODERATE","HIGH","CRITICAL"])
    if facilities: work=work[work.facility_name.isin(facilities)]
    if bands: work=work[work.risk_band.isin(bands)]
    st.dataframe(work,use_container_width=True,hide_index=True)
    st.download_button("⬇ Download screened CSV",work.to_csv(index=False).encode(),"wastewater_screened_records.csv","text/csv",use_container_width=True)

# ---------- Methodology ----------
else:
    st.markdown('<div class="card"><div class="cardtitle">⚙️ Methodology & System</div><div class="muted">Transparent architecture, screening logic and responsible-use guidance.</div></div>',unsafe_allow_html=True)
    st.markdown("""
### Architecture
- **Streamlit** — dashboard and controls
- **Pandas** — local CSV processing
- **NumPy** — deterministic scoring
- **Plotly** — interactive analytics
- **CSV** — local data storage
- No external APIs or cloud database

### Screening model
The 0–100 score combines:
- configured chemical reference-range signals
- flow intensity
- treatment-performance gap
- weather context
- inspection status
- corrective-action status
- inspection age
- discharge duration

### Risk bands
- **0–34:** LOW
- **35–54:** MODERATE
- **55–71:** HIGH
- **72–100:** CRITICAL

The reference ranges in this demonstration are **screening values only**. Regulatory limits vary by jurisdiction, permit, receiving environment and facility. The system does not certify compliance or determine a legal violation.
""")
    st.markdown('<div class="info"><b>Local-first:</b> uploaded CSV records are processed within this local Python application. Use official permits, applicable regulations and qualified environmental/compliance professionals for real decisions.</div>',unsafe_allow_html=True)

st.markdown('<div class="footer">Industrial Wastewater Compliance Monitor • Advanced local-first environmental intelligence</div>',unsafe_allow_html=True)
