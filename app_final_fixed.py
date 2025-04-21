
import streamlit as st
import math
import plotly.graph_objects as go
import plotly.io as pio
from fpdf import FPDF
import tempfile

def main_app_content():
    def calculate_smart2_risk(sbp, tc, hdl, egfr, crp, smoker, diabetes):
        age = st.session_state.age
        sex = 1 if st.session_state.sex == "Male" else 0
        beds = sum([
            st.session_state.vascular_cad,
            st.session_state.vascular_cev,
            st.session_state.vascular_pad
        ])

        lp = (
            0.0651 * age +
            0.470 * sex +
            0.562 * smoker +
            0.661 * diabetes +
            0.00199 * sbp +
           -0.295 * hdl +
            0.124 * tc +
           -0.0159 * egfr +
            0.145 * beds +
            0.150 * math.log(crp + 1)
        ) - 7.2046

        s10 = 0.8707
        slt = 0.600
        s5 = pow(s10, 0.5)

        r5 = 1 - pow(s5, math.exp(lp))
        r10 = 1 - pow(s10, math.exp(lp))
        rlt = 1 - pow(slt, math.exp(lp))

        return round(r5 * 100, 1), round(r10 * 100, 1), round(rlt * 100, 1)

    # Inputs (example defaults for local testing)
    if 'age' not in st.session_state:
        st.session_state.age = 60
        st.session_state.sex = 'Male'
        st.session_state.sbp = 140
        st.session_state.tc = 5.5
        st.session_state.hdl = 1.3
        st.session_state.egfr = 90
        st.session_state.crp = 2.5
        st.session_state.smoker = False
        st.session_state.diabetes = False
        st.session_state.hypertension = True
        st.session_state.new_statin = 'Atorvastatin'
        st.session_state.new_ez = True
        st.session_state.pcsk9 = False
        st.session_state.inclisiran = False
        st.session_state.new_lifestyle = True
        st.session_state.smoking_cease = True
        st.session_state.vascular_cad = True
        st.session_state.vascular_cev = False
        st.session_state.vascular_pad = True

    base_vals = {
        'sbp': st.session_state.sbp,
        'tc': st.session_state.tc,
        'hdl': st.session_state.hdl,
        'egfr': st.session_state.egfr,
        'crp': st.session_state.crp,
        'smoker': 1 if st.session_state.smoker else 0,
        'diabetes': 1 if st.session_state.diabetes else 0
    }

    base_5y, base_10y, base_life = calculate_smart2_risk(**base_vals)

    interv_vals = base_vals.copy()
    if st.session_state.hypertension:
        interv_vals['sbp'] -= 10
    if any([st.session_state.new_statin != 'None', st.session_state.new_ez,
            st.session_state.pcsk9, st.session_state.inclisiran]):
        interv_vals['tc'] -= 1.0
    if st.session_state.new_lifestyle:
        interv_vals['crp'] -= 0.5
    if st.session_state.smoker and st.session_state.smoking_cease:
        interv_vals['smoker'] = 0

    intv_5y, intv_10y, intv_life = calculate_smart2_risk(**interv_vals)

    st.subheader("📉 SMART2 Risk With and Without Intervention")
    st.metric("Baseline 10-Year Risk", f"{base_10y}%")
    st.metric("With Intervention (10y)", f"{intv_10y}%")
    st.metric("ARR (10y)", f"{round(base_10y - intv_10y, 1)}%")
    st.metric("Baseline Lifetime Risk", f"{base_life}%")
    st.metric("With Intervention (Lifetime)", f"{intv_life}%")
    st.metric("ARR (Lifetime)", f"{round(base_life - intv_life, 1)}%")

    st.subheader("📊 Visual Risk Comparison")
    period = st.selectbox("Select timeframe to compare:", ["5-Year", "10-Year", "Lifetime"], index=1)
    x = ["Baseline", "With Intervention"]
    y = [base_10y, intv_10y] if period == "10-Year" else [base_5y, intv_5y] if period == "5-Year" else [base_life, intv_life]

    fig = go.Figure()
    fig.add_trace(go.Bar(x=x, y=y, text=[f"{val}%" for val in y], textposition='auto'))
    fig.update_layout(yaxis_title="Risk (%)", title=f"{period} Risk Comparison", template="plotly_white")
    st.plotly_chart(fig, use_container_width=True)

    if st.button("📄 Export summary as PDF"):
        with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp_img:
            pio.write_image(fig, tmp_img.name, format="png")
            chart_path = tmp_img.name

        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", size=12)
        pdf.cell(200, 10, txt="SMART2 Risk Summary", ln=1, align="C")
        for label, val1, val2 in zip(["5-Year", "10-Year", "Lifetime"], [base_5y, base_10y, base_life], [intv_5y, intv_10y, intv_life]):
            arr = round(val1 - val2, 1)
            pdf.ln(5)
            pdf.cell(0, 10, f"Baseline {label} Risk: {val1}%", ln=True)
            pdf.cell(0, 10, f"With Intervention: {val2}% | ARR: {arr}%", ln=True)

        pdf.image(chart_path, x=10, y=None, w=180)
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as f:
            pdf.output(f.name)
            with open(f.name, "rb") as pdf_file:
                st.download_button(label="Download PDF", data=pdf_file, file_name="smart2_risk_summary.pdf", mime="application/pdf")

if __name__ == "__main__":
    main_app_content()
