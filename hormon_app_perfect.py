# hormon_app_perfect.py
import streamlit as st
import numpy as np
import pandas as pd
import plotly.graph_objects as go
from scipy.interpolate import interp1d
from datetime import datetime
import json
import io
import sys
import subprocess

# Streamlit саҳифа конфигурацияси - ФАҚАТ БИТТА МАРТА
st.set_page_config(
    page_title="Гормон Калибровка Тизими",
    page_icon="🧪",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS стиллар
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Roboto:wght@300;400;500;700&display=swap');
    
    * {
        font-family: 'Roboto', sans-serif;
    }
    
    .main-header {
        font-size: 2.8rem;
        color: #2E86AB;
        text-align: center;
        margin-bottom: 2rem;
        padding: 20px;
        background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
        border-radius: 15px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    
    .sub-header {
        font-size: 2rem;
        color: #A23B72;
        margin-top: 1.5rem;
        margin-bottom: 1rem;
        padding-bottom: 10px;
        border-bottom: 3px solid #A23B72;
    }
    
    .stButton > button {
        background-color: #2E86AB;
        color: white;
        font-weight: bold;
        border-radius: 8px;
        padding: 10px 24px;
        border: none;
        transition: all 0.3s ease;
    }
    
    .stButton > button:hover {
        background-color: #1B5D7A;
        transform: translateY(-2px);
        box-shadow: 0 4px 8px rgba(0,0,0,0.2);
    }
    
    .success-box {
        background-color: #d4edda;
        border: 1px solid #c3e6cb;
        border-radius: 10px;
        padding: 15px;
        margin: 10px 0;
    }
    
    .warning-box {
        background-color: #fff3cd;
        border: 1px solid #ffeaa7;
        border-radius: 10px;
        padding: 15px;
        margin: 10px 0;
    }
    
    .info-box {
        background-color: #d1ecf1;
        border: 1px solid #bee5eb;
        border-radius: 10px;
        padding: 15px;
        margin: 10px 0;
    }
    
    .dataframe {
        border-radius: 10px;
        overflow: hidden;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    
    .stNumberInput input {
        border-radius: 8px !important;
    }
    
    .menu-button {
        width: 100%;
        margin: 5px 0;
    }
    
    .download-button {
        background-color: #28a745 !important;
    }
    
    .clear-button {
        background-color: #dc3545 !important;
    }
</style>
""", unsafe_allow_html=True)

# Excel экспорт учун функция
def check_excel_support():
    """Excel экспортни қўллаб-қувватлашни текшириш"""
    try:
        import xlsxwriter
        return True
    except ImportError:
        return False

def install_xlsxwriter():
    """xlsxwriter ни ўрнатиш"""
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "xlsxwriter", "--quiet"])
        return True
    except:
        return False

def export_to_excel(results_df, статистика, гормон_номи):
    """Excel файл яратиш"""
    try:
        # Автоматик ўрнатиш
        if not check_excel_support():
            if install_xlsxwriter():
                st.success("✅ xlsxwriter ўрнатилди")
            else:
                st.warning("⚠️ xlsxwriter ўрнатишда хатолик. CSV форматида юклаб олинг.")
                return None
        
        import xlsxwriter
        from io import BytesIO
        
        output = BytesIO()
        
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            # Натижаларни ёзиш
            results_df.to_excel(writer, sheet_name='Натижалар', index=False)
            
            # Статистикани ёзиш
            stats_df = pd.DataFrame(list(статистика.items()), columns=['Параметр', 'Қиймат'])
            stats_df.to_excel(writer, sheet_name='Статистика', index=False)
            
            # Форматлаш
            workbook = writer.book
            
            # Сарлавҳа формати
            header_format = workbook.add_format({
                'bold': True,
                'border': 1,
                'bg_color': '#2E86AB',
                'color': 'white',
                'align': 'center'
            })
            
            # Ҳолат формати
            normal_format = workbook.add_format({
                'bg_color': '#d4edda',
                'border': 1,
                'align': 'center'
            })
            
            warning_format = workbook.add_format({
                'bg_color': '#fff3cd',
                'border': 1,
                'align': 'center'
            })
            
            # Форматларни қўллаш
            worksheet = writer.sheets['Натижалар']
            for col_num, value in enumerate(results_df.columns.values):
                worksheet.write(0, col_num, value, header_format)
            
            # Ҳолатларга ранг бериш
            if 'Ҳолат' in results_df.columns:
                col_idx = results_df.columns.get_loc('Ҳолат')
                for row_num in range(1, len(results_df) + 1):
                    cell_value = results_df.iloc[row_num-1, col_idx]
                    if '✅' in str(cell_value):
                        worksheet.write(row_num, col_idx, cell_value, normal_format)
                    elif '⚠️' in str(cell_value):
                        worksheet.write(row_num, col_idx, cell_value, warning_format)
        
        return output.getvalue()
        
    except Exception as e:
        st.error(f"❌ Excel экспортда хатолик: {str(e)[:100]}")
        return None

# Функцияларни эълон қилиш
def интерполяция(оптик_зичлик_стандарт, концентрация_стандарт, оптик_зичлик_беморлар, усул='linear'):
    """
    Интерполяция функцияси
    """
    try:
        оптик_зичлик_стандарт = np.array(оптик_зичлик_стандарт, dtype=float)
        концентрация_стандарт = np.array(концентрация_стандарт, dtype=float)
        оптик_зичлик_беморлар = np.array(оптик_зичлик_беморлар, dtype=float)
        
        # Тартиблаш
        tartib = np.argsort(оптик_зичлик_стандарт)
        оптик_зичлик_стандарт = оптик_зичлик_стандарт[tartib]
        концентрация_стандарт = концентрация_стандарт[tartib]
        
        if усул == 'linear':
            f = interp1d(оптик_зичлик_стандарт, концентрация_стандарт, fill_value="extrapolate")
        elif усул == 'spline':
            f = interp1d(оптик_зичлик_стандарт, концентрация_стандарт, kind='cubic', fill_value="extrapolate")
        elif усул == 'quadratic':
            f = interp1d(оптик_зичлик_стандарт, концентрация_стандарт, kind='quadratic', fill_value="extrapolate")
        else:
            raise ValueError("Номаълум интерполяция усули")
        
        концентрация_беморлар = f(оптик_зичлик_беморлар)
        
        # Ҳолатни аниқлаш
        сақлаш_холати = np.zeros_like(концентрация_беморлар, dtype=int)
        if len(оптик_зичлик_стандарт) > 0:
            min_val = оптик_зичлик_стандарт.min()
            max_val = оптик_зичлик_стандарт.max()
            сақлаш_холати[оптик_зичлик_беморлар < min_val] = -1
            сақлаш_холати[оптик_зичлик_беморлар > max_val] = 1
        
        return концентрация_беморлар, сақлаш_холати
        
    except Exception as e:
        st.error(f"Интерполяцияда хатолик: {str(e)[:100]}")
        return np.full_like(оптик_зичлик_беморлар, np.nan), np.zeros_like(оптик_зичлик_беморлар, dtype=int)

def create_calibration_plot(оптик_зичлик_стандарт, концентрация_стандарт, 
                          оптик_зичлик_беморлар, концентрация_беморлар, 
                          гормон_номи, улчов_бирлиги, сақлаш_холати):
    """
    Interactive Plotly график яратиш
    """
    fig = go.Figure()
    
    # Калибровка қийшиқ чизиғи
    if len(оптик_зичлик_стандарт) > 0:
        fig.add_trace(go.Scatter(
            x=оптик_зичлик_стандарт,
            y=концентрация_стандарт,
            mode='lines+markers',
            name='Стандартлар',
            line=dict(color='blue', width=3),
            marker=dict(size=10, color='blue', symbol='square')
        ))
    
    # Беморлар натижалари
    colors = ['green', 'red', 'orange']
    labels = ['Беморлар (нормал)', 'Беморлар (пастки диапазон)', 'Беморлар (юкори диапазон)']
    
    for i, (color, label) in enumerate(zip(colors, labels)):
        mask = сақлаш_холати == (i-1)
        if np.any(mask):
            fig.add_trace(go.Scatter(
                x=оптик_зичлик_беморлар[mask],
                y=концентрация_беморлар[mask],
                mode='markers',
                name=label,
                marker=dict(size=12, color=color, symbol='circle', 
                          line=dict(width=2, color='white'))
            ))
    
    # Диапазон чизиқлари
    if len(оптик_зичлик_стандарт) > 0:
        fig.add_vline(x=min(оптик_зичлик_стандарт), line_dash="dash", 
                     line_color="red", opacity=0.5, annotation_text="Минимал диапазон")
        fig.add_vline(x=max(оптик_зичлик_стандарт), line_dash="dash", 
                     line_color="red", opacity=0.5, annotation_text="Максимал диапазон")
    
    fig.update_layout(
        title=f'{гормон_номи} калибровка қийшиқ чизиғи',
        xaxis_title='Оптик зичлик',
        yaxis_title=f'Концентрация ({улчов_бирлиги})',
        height=600,
        hovermode='x unified',
        template='plotly_white',
        plot_bgcolor='rgba(240,242,246,0.8)',
        paper_bgcolor='rgba(255,255,255,0.9)',
        font=dict(size=14)
    )
    
    return fig

# Сессия стейтини инициализация қилиш
if 'initialized' not in st.session_state:
    st.session_state.initialized = True
    st.session_state.гормон_номи = "TSH"
    st.session_state.улчов_бирлиги = "мкМЕ/мл"
    st.session_state.стандарт_маълумотлари = [[0.1, 1.0], [0.2, 2.0], [0.3, 3.0], [0.4, 4.0], [0.5, 5.0]]
    st.session_state.беморлар_маълумотлари = [0.15, 0.25, 0.35, 0.45, 0.55, 0.65, 0.75, 0.85, 0.95, 1.05]
    st.session_state.calculated = False
    st.session_state.results_df = None
    st.session_state.статистика = {}

# САҲИФАНИ ТЕКШИРИШ
st.markdown('<h1 class="main-header">🧪 ГОРМОН КАЛИБРОВКА ТИЗИМИ</h1>', unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    st.markdown("""
    <div style='background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                padding: 20px; border-radius: 10px; color: white; margin-bottom: 20px;'>
        <h3 style='color: white;'>⚙️ Созламалар</h3>
    </div>
    """, unsafe_allow_html=True)
    
    усул = st.selectbox(
        "Интерполяция усули",
        ["linear", "spline", "quadratic"],
        index=0,
        key="interpolation_method"
    )
    
    st.markdown("---")
    
    # Меню тугмалари
    st.markdown("### 📁 Меню")
    
    # Streamlit версиясини текшириш ва унига қараб rerun танлаш
    try:
        # Streamlit 1.28.0 ва ундан юқори версиялар учун
        from streamlit import rerun as st_rerun
        use_rerun = True
    except:
        # Эски версиялар учун
        use_rerun = False
    
    if st.button("🔄 Мисол маълумотлари", 
                use_container_width=True,
                key="load_example_data"):
        st.session_state.гормон_номи = "TSH"
        st.session_state.улчов_бирлиги = "мкМЕ/мл"
        st.session_state.стандарт_маълумотлари = [[0.1, 1.0], [0.2, 2.0], [0.3, 3.0], [0.4, 4.0], [0.5, 5.0]]
        st.session_state.беморлар_маълумотлари = [0.15, 0.25, 0.35, 0.45, 0.55, 0.65, 0.75, 0.85, 0.95, 1.05]
        st.session_state.calculated = False
        st.session_state.results_df = None
        
        # Rerun логикаси
        if use_rerun:
            st_rerun()
        else:
            st.experimental_rerun()
    
    if st.button("🗑️ Барча маълумотларни тозалаш", 
                use_container_width=True,
                key="clear_all_data"):
        st.session_state.стандарт_маълумотлари = [[0.1, 1.0], [0.2, 2.0], [0.3, 3.0]]
        st.session_state.беморлар_маълумотлари = [0.15, 0.25, 0.35]
        st.session_state.calculated = False
        st.session_state.results_df = None
        
        # Rerun логикаси
        if use_rerun:
            st_rerun()
        else:
            st.experimental_rerun()
    
    # Excel ўрнатиш
    st.markdown("---")
    if st.button("📦 Excel ўрнатиш (xlsxwriter)", 
                use_container_width=True,
                key="install_xlsxwriter"):
        with st.spinner("xlsxwriter ўрнатилмоқда..."):
            if install_xlsxwriter():
                st.success("✅ xlsxwriter ўрнатилди!")
                # Фойдаланувчига янгилаш кераклигини айтиш
                st.info("Илтимос, саҳифани қўлда янгиланг (F5 ёки браузернинг 'Refresh' тугмаси)")
            else:
                st.error("❌ xlsxwriter ўрнатишда хатолик")

# Основной интерфейс
tab1, tab2, tab3, tab4 = st.tabs(["📊 Стандартлар", "👥 Беморлар", "📈 Натижалар", "💾 Экспорт"])

with tab1:
    st.markdown('<h3 class="sub-header">Стандарт маълумотлари</h3>', unsafe_allow_html=True)
    
    st.markdown('<div class="info-box">Стандарт маълумотлари - гормон калибровкаси учун асосий маълумотлар</div>', unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([2, 2, 1])
    
    with col1:
        гормон_номи = st.text_input("Гормон номи", 
                                   value=st.session_state.гормон_номи,
                                   key="hormon_name_input")
        st.session_state.гормон_номи = гормон_номи
        
    with col2:
        улчов_бирлиги = st.text_input("Ўлчов бирлиги", 
                                     value=st.session_state.улчов_бирлиги,
                                     key="unit_input")
        st.session_state.улчов_бирлиги = улчов_бирлиги
    
    with col3:
        if st.button("♻️ Тозалаш", 
                    use_container_width=True,
                    key="clear_standards_only"):
            st.session_state.стандарт_маълумотлари = [[0.1, 1.0], [0.2, 2.0], [0.3, 3.0]]
            # Rerun логикаси
            if use_rerun:
                st_rerun()
            else:
                st.experimental_rerun()
    
    стандартлар_сони = st.number_input("Стандартлар сони", 
                                       min_value=3, 
                                       max_value=10, 
                                       value=5, 
                                       key="стандарт_сони_input")
    
    # Стандарт маълумотларини киритиш
    st.markdown("### Оптик зичлик ва концентрация киритиш:")
    
    # Текшириш ва тузатиш
    current_standard_data = st.session_state.стандарт_маълумотлари.copy()
    if len(current_standard_data) < стандартлар_сони:
        for i in range(len(current_standard_data), стандартлар_сони):
            current_standard_data.append([0.1 * (i+1), 1.0 * (i+1)])
    elif len(current_standard_data) > стандартлар_сони:
        current_standard_data = current_standard_data[:стандартлар_сони]
    
    new_standard_data = []
    for i in range(стандартлар_сони):
        cols = st.columns(2)
        
        with cols[0]:
            if i < len(current_standard_data):
                default_opt = float(current_standard_data[i][0])
            else:
                default_opt = 0.1 * (i+1)
            
            оптик = st.number_input(
                f"Оптик зичлик {i+1}", 
                value=default_opt, 
                min_value=0.0,
                max_value=10.0,
                step=0.01,
                key=f"opt_input_{i}"
            )
        
        with cols[1]:
            if i < len(current_standard_data):
                default_conc = float(current_standard_data[i][1])
            else:
                default_conc = 1.0 * (i+1)
            
            концентрация = st.number_input(
                f"Концентрация {i+1}", 
                value=default_conc, 
                min_value=0.0,
                max_value=1000.0,
                step=0.1,
                key=f"conc_input_{i}"
            )
        
        new_standard_data.append([оптик, концентрация])
    
    # Сақлаш
    st.session_state.стандарт_маълумотлари = new_standard_data
    
    # Таблица
    st.markdown("### Стандартлар жадвали:")
    стандарт_df = pd.DataFrame(
        new_standard_data, 
        columns=["Оптик зичлик", f"Концентрация ({улчов_бирлиги})"]
    )
    
    st.dataframe(стандарт_df.style.format({
        "Оптик зичлик": "{:.3f}", 
        f"Концентрация ({улчов_бирлиги})": "{:.3f}"
    }), use_container_width=True)

with tab2:
    st.markdown('<h3 class="sub-header">Беморлар маълумотлари</h3>', unsafe_allow_html=True)
    
    st.markdown('<div class="info-box">Беморларнинг оптик зичликларини киритинг</div>', unsafe_allow_html=True)
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        беморлар_сони = st.number_input("Беморлар сони", 
                                       min_value=1, 
                                       max_value=50, 
                                       value=10, 
                                       key="бемор_сони_input")
    
    with col2:
        if st.button("🗑️ Тозалаш", 
                    use_container_width=True,
                    key="clear_patients_only"):
            st.session_state.беморлар_маълумотлари = [0.15, 0.25, 0.35]
            # Rerun логикаси
            if use_rerun:
                st_rerun()
            else:
                st.experimental_rerun()
    
    # Бемор маълумотларини киритиш
    st.markdown("### Беморлар оптик зичликлари:")
    
    # Текшириш ва тузатиш
    current_patient_data = st.session_state.беморлар_маълумотлари.copy()
    if len(current_patient_data) < беморлар_сони:
        for i in range(len(current_patient_data), беморлар_сони):
            current_patient_data.append(0.5 + (i * 0.05))
    elif len(current_patient_data) > беморлар_сони:
        current_patient_data = current_patient_data[:беморлар_сони]
    
    patient_data = []
    for i in range(беморлар_сони):
        cols = st.columns([1, 3])
        
        with cols[0]:
            st.markdown(f"**Бемор {i+1}**")
        
        with cols[1]:
            if i < len(current_patient_data):
                default_value = float(current_patient_data[i])
            else:
                default_value = 0.5 + (i * 0.05)
            
            оптик = st.number_input(
                f"Оптик зичлик {i+1}",
                value=default_value,
                min_value=0.0,
                max_value=10.0,
                step=0.001,
                format="%.4f",
                key=f"patient_opt_input_{i}",
                label_visibility="collapsed"
            )
        
        patient_data.append([i+1, оптик])
    
    # Сақлаш
    st.session_state.беморлар_маълумотлари = [data[1] for data in patient_data]
    
    # Таблица
    if patient_data:
        st.markdown("### Беморлар жадвали:")
        беморлар_df = pd.DataFrame(patient_data, columns=["Бемор №", "Оптик зичлик"])
        
        st.dataframe(беморлар_df.style.format({
            "Оптик зичлик": "{:.4f}"
        }), use_container_width=True)

with tab3:
    st.markdown('<h3 class="sub-header">Ҳисоблаш натижалари</h3>', unsafe_allow_html=True)
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        if st.button("🎯 ҲИСОБЛАШ", 
                    type="primary", 
                    use_container_width=True,
                    key="calculate_button"):
            with st.spinner("Ҳисоблаш жараёнида..."):
                try:
                    # Маълумотлар
                    оптик_зичлик_стандарт = np.array([x[0] for x in st.session_state.стандарт_маълумотлари])
                    концентрация_стандарт = np.array([x[1] for x in st.session_state.стандарт_маълумотлари])
                    оптик_зичлик_беморлар = np.array(st.session_state.беморлар_маълумотлари[:беморлар_сони])
                    
                    # Интерполяция
                    концентрация_беморлар, сақлаш_холати = интерполяция(
                        оптик_зичлик_стандарт,
                        концентрация_стандарт,
                        оптик_зичлик_беморлар,
                        усул
                    )
                    
                    # Статистика
                    статистика = {
                        "Жами беморлар": len(концентрация_беморлар),
                        "Нормал диапазонда": int(np.sum(сақлаш_холати == 0)),
                        "Пастки диапазон": int(np.sum(сақлаш_холати == -1)),
                        "Юкори диапазон": int(np.sum(сақлаш_холати == 1)),
                    }
                    
                    # Натижалар
                    results_data = []
                    for i in range(len(концентрация_беморлар)):
                        if сақлаш_холати[i] == 0:
                            status = "✅ Нормал"
                        elif сақлаш_холати[i] == -1:
                            status = "⚠️ Пастки"
                        else:
                            status = "⚠️ Юкори"
                        
                        conc_value = концентрация_беморлар[i]
                        if np.isnan(conc_value):
                            conc_text = "N/A"
                        else:
                            conc_text = f"{conc_value:.4f}"
                        
                        results_data.append([
                            i+1,
                            оптик_зичлик_беморлар[i],
                            conc_text,
                            status
                        ])
                    
                    results_df = pd.DataFrame(
                        results_data,
                        columns=["Бемор №", "Оптик зичлик", f"Концентрация ({st.session_state.улчов_бирлиги})", "Ҳолат"]
                    )
                    
                    # Сақлаш
                    st.session_state.results_df = results_df
                    st.session_state.статистика = статистика
                    st.session_state.концентрация_беморлар = концентрация_беморлар
                    st.session_state.сақлаш_холати = сақлаш_холати
                    st.session_state.оптик_зичлик_стандарт = оптик_зичлик_стандарт
                    st.session_state.концентрация_стандарт = концентрация_стандарт
                    st.session_state.оптик_зичлик_беморлар = оптик_зичлик_беморлар
                    st.session_state.calculated = True
                    
                    st.success("✅ Ҳисоблаш муваффақиятли тугади!")
                    
                except Exception as e:
                    st.error(f"❌ Ҳисоблашда хатолик: {str(e)[:100]}")
    
    with col2:
        if st.button("🗑️ Тозалаш", 
                    use_container_width=True,
                    key="clear_results"):
            st.session_state.calculated = False
            st.session_state.results_df = None
            # Rerun логикаси
            if use_rerun:
                st_rerun()
            else:
                st.experimental_rerun()
    
    # Натижаларни кўрсатиш
    if st.session_state.calculated:
        results_df = st.session_state.results_df
        
        st.markdown('<div class="success-box">✅ Ҳисоблаш муваффақиятли амалга оширилди!</div>', unsafe_allow_html=True)
        
        # Таблица
        st.markdown("### Беморлар натижалари:")
        
        # Стиллаш функцияси - .applymap() ўрнига .map() ишлатилди
        def color_status(val):
            if '✅' in str(val):
                return 'background-color: #d4edda; color: #155724; font-weight: bold;'
            elif '⚠️' in str(val):
                return 'background-color: #fff3cd; color: #856404; font-weight: bold;'
            return ''
        
        # .applymap() ўрнига .map() ишлатилди
        styled_df = results_df.style.map(color_status, subset=['Ҳолат'])
        st.dataframe(styled_df, use_container_width=True)
        
        # График
        st.markdown("### Калибровка графиги:")
        fig = create_calibration_plot(
            st.session_state.оптик_зичлик_стандарт,
            st.session_state.концентрация_стандарт,
            st.session_state.оптик_зичлик_беморлар,
            st.session_state.концентрация_беморлар,
            st.session_state.гормон_номи,
            st.session_state.улчов_бирлиги,
            st.session_state.сақлаш_холати
        )
        st.plotly_chart(fig, use_container_width=True)
        
        # Статистика
        st.markdown('<h4>📊 Статистика</h4>', unsafe_allow_html=True)
        
        stat_items = list(st.session_state.статистика.items())
        cols = st.columns(min(4, len(stat_items)))
        
        for idx, (key, value) in enumerate(stat_items):
            col_idx = idx % len(cols)
            with cols[col_idx]:
                st.metric(label=key, value=value)
    else:
        st.markdown('<div class="warning-box">ℹ️ Ҳисоблаш учун "🎯 ҲИСОБЛАШ" тугмасини босинг.</div>', unsafe_allow_html=True)

with tab4:
    st.markdown('<h3 class="sub-header">Экспорт ва сақлаш</h3>', unsafe_allow_html=True)
    
    if st.session_state.calculated:
        # Натижаларни юклаб олиш
        st.markdown("### 📥 Натижаларни юклаб олиш")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            # CSV формати
            csv = st.session_state.results_df.to_csv(index=False).encode('utf-8-sig')
            st.download_button(
                label="📄 CSV форматида",
                data=csv,
                file_name=f"{st.session_state.гормон_номи}_натижалари.csv",
                mime="text/csv",
                use_container_width=True,
                key="download_csv"
            )
        
        with col2:
            # Excel формати
            excel_data = export_to_excel(
                st.session_state.results_df,
                st.session_state.статистика,
                st.session_state.гормон_номи
            )
            
            if excel_data:
                st.download_button(
                    label="📊 Excel форматида",
                    data=excel_data,
                    file_name=f"{st.session_state.гормон_номи}_натижалари.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True,
                    key="download_excel"
                )
            else:
                st.info("Excel учун 'Excel ўрнатиш' тугмасини босинг")
        
        with col3:
            # JSON конфигурация
            config_data = {
                "гормон_номи": st.session_state.гормон_номи,
                "улчов_бирлиги": st.session_state.улчов_бирлиги,
                "стандартлар": st.session_state.стандарт_маълумотлари,
                "беморлар": st.session_state.беморлар_маълумотлари,
                "интерполяция_усули": усул,
                "сақлаш_вақти": datetime.now().isoformat()
            }
            
            config_json = json.dumps(config_data, indent=2, ensure_ascii=False)
            
            st.download_button(
                label="⚙️ JSON конфигурация",
                data=config_json,
                file_name=f"{st.session_state.гормон_номи}_конфигурация.json",
                mime="application/json",
                use_container_width=True,
                key="download_config"
            )
        
        # Натижаларни кўриш
        st.markdown("### 👁️ Натижаларни кўриш")
        st.dataframe(st.session_state.results_df, use_container_width=True)
        
    else:
        st.markdown('<div class="warning-box">ℹ️ Аввало ҳисоблаш амалиётини бажаринг.</div>', unsafe_allow_html=True)

# Футер
st.markdown("---")
st.markdown("""
<div style='text-align: center; padding: 20px; color: #666;'>
    <p>🧪 Гормон Калибровка Тизими | Version 3.2 | © 2024</p>
    <p style='font-size: 0.8rem; color: #999;'>Streamlit версияси: {}</p>
</div>
""".format(st.__version__), unsafe_allow_html=True)
