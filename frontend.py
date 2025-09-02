import streamlit as st
import streamlit.components.v1 as components

def load_custom_css():
    """CSS compatible con modo claro y oscuro de Streamlit con animaciones"""
    st.markdown("""
    <style>
    /* Variables CSS para modo claro y oscuro */
    :root {
        --primary-color: #3b82f6;
        --primary-dark: #1e40af;
        --success-color: #059669;
        --warning-color: #d97706;
        --danger-color: #dc2626;
        --text-primary: #1f2937;
        --text-secondary: #6b7280;
        --bg-primary: #ffffff;
        --bg-secondary: #f8fafc;
        --bg-accent: #f0f9ff;
        --border-color: #e5e7eb;
        --shadow: rgba(0, 0, 0, 0.1);
    }
    
    /* Modo oscuro */
    @media (prefers-color-scheme: dark) {
        :root {
            --text-primary: #f9fafb;
            --text-secondary: #d1d5db;
            --bg-primary: #1f2937;
            --bg-secondary: #374151;
            --bg-accent: #1e3a8a;
            --border-color: #4b5563;
            --shadow: rgba(0, 0, 0, 0.3);
        }
    }
    
    /* Detección automática del tema de Streamlit */
    [data-theme="dark"] {
        --text-primary: #f9fafb;
        --text-secondary: #d1d5db;
        --bg-primary: #1f2937;
        --bg-secondary: #374151;
        --bg-accent: #1e3a8a;
        --border-color: #4b5563;
        --shadow: rgba(0, 0, 0, 0.3);
    }
    
    /* Agregando animaciones globales y keyframes */
    @keyframes fadeInUp {
        from {
            opacity: 0;
            transform: translateY(30px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }
    
    @keyframes slideInLeft {
        from {
            opacity: 0;
            transform: translateX(-30px);
        }
        to {
            opacity: 1;
            transform: translateX(0);
        }
    }
    
    @keyframes pulse {
        0%, 100% {
            transform: scale(1);
        }
        50% {
            transform: scale(1.05);
        }
    }
    
    @keyframes bounce {
        0%, 20%, 50%, 80%, 100% {
            transform: translateY(0);
        }
        40% {
            transform: translateY(-10px);
        }
        60% {
            transform: translateY(-5px);
        }
    }
    
    @keyframes shimmer {
        0% {
            background-position: -200px 0;
        }
        100% {
            background-position: calc(200px + 100%) 0;
        }
    }
    
    /* Header principal con animación */
    .main-header {
        background: linear-gradient(90deg, var(--primary-dark) 0%, var(--primary-color) 100%);
        padding: 2rem;
        border-radius: 10px;
        margin-bottom: 2rem;
        text-align: center;
        color: white;
        box-shadow: 0 4px 6px var(--shadow);
        animation: fadeInUp 0.8s ease-out;
        transition: all 0.3s ease;
    }
    
    .main-header:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 25px var(--shadow);
    }
    
    .main-header h1 {
        margin: 0;
        font-size: 2.5rem;
        font-weight: 700;
        animation: bounce 2s infinite;
    }
    
    .main-header p {
        margin: 0.5rem 0 0 0;
        font-size: 1.1rem;
        opacity: 0.9;
        animation: fadeInUp 1s ease-out 0.3s both;
    }
    
    /* Secciones con animaciones de entrada */
    .section-header {
        background: var(--bg-secondary);
        padding: 1rem 1.5rem;
        border-radius: 8px;
        border-left: 4px solid var(--primary-color);
        margin: 1.5rem 0 1rem 0;
        animation: slideInLeft 0.6s ease-out;
        transition: all 0.3s ease;
        cursor: pointer;
    }
    
    .section-header:hover {
        transform: translateX(5px);
        box-shadow: 0 4px 12px var(--shadow);
        border-left-width: 6px;
    }
    
    .section-header h3 {
        margin: 0;
        color: var(--primary-dark);
        font-weight: 600;
        transition: color 0.3s ease;
    }
    
    .section-header:hover h3 {
        color: var(--primary-color);
    }
    
    /* Métricas con efectos hover y animaciones */
    .metric-container {
        background: var(--bg-primary);
        padding: 1.5rem;
        border-radius: 10px;
        box-shadow: 0 2px 4px var(--shadow);
        border: 1px solid var(--border-color);
        text-align: center;
        margin: 0.5rem 0;
        animation: fadeInUp 0.6s ease-out;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        cursor: pointer;
        position: relative;
        overflow: hidden;
    }
    
    .metric-container::before {
        content: '';
        position: absolute;
        top: 0;
        left: -200px;
        width: 200px;
        height: 100%;
        background: linear-gradient(90deg, transparent, rgba(255,255,255,0.2), transparent);
        transition: left 0.5s;
    }
    
    .metric-container:hover::before {
        left: 100%;
    }
    
    .metric-container:hover {
        transform: translateY(-8px) scale(1.02);
        box-shadow: 0 12px 25px var(--shadow);
        border-color: var(--primary-color);
    }
    
    .metric-value {
        font-size: 2.5rem;
        font-weight: 700;
        margin: 0;
        transition: all 0.3s ease;
    }
    
    .metric-container:hover .metric-value {
        transform: scale(1.1);
        text-shadow: 0 2px 4px var(--shadow);
    }
    
    .metric-nuevos { 
        color: var(--success-color);
    }
    .metric-mantenidos { 
        color: var(--primary-color);
    }
    .metric-eliminados { 
        color: var(--danger-color);
    }
    .metric-modificados { 
        color: var(--warning-color);
    }
    
    .metric-container:hover .metric-nuevos {
        color: #10b981;
        animation: pulse 1.5s infinite;
    }
    
    .metric-container:hover .metric-mantenidos {
        color: #60a5fa;
        animation: pulse 1.5s infinite;
    }
    
    .metric-container:hover .metric-eliminados {
        color: #f87171;
        animation: pulse 1.5s infinite;
    }
    
    .metric-container:hover .metric-modificados {
        color: #fde68a;
        animation: pulse 1.5s infinite;
    }
    
    .metric-label {
        font-size: 0.9rem;
        color: var(--text-secondary);
        margin: 0.5rem 0 0 0;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        transition: all 0.3s ease;
    }
    
    .metric-container:hover .metric-label {
        color: var(--text-primary);
        transform: translateY(-2px);
    }
    
    /* Alertas con animaciones de entrada */
    .alert-success, .alert-warning, .alert-info {
        border-radius: 8px;
        padding: 1rem;
        margin: 1rem 0;
        animation: slideInLeft 0.5s ease-out;
        transition: all 0.3s ease;
        cursor: pointer;
        position: relative;
        overflow: hidden;
    }
    
    .alert-success {
        background: color-mix(in srgb, var(--success-color) 10%, var(--bg-primary));
        border: 1px solid color-mix(in srgb, var(--success-color) 30%, var(--bg-primary));
        color: var(--success-color);
    }
    
    .alert-warning {
        background: color-mix(in srgb, var(--warning-color) 10%, var(--bg-primary));
        border: 1px solid color-mix(in srgb, var(--warning-color) 30%, var(--bg-primary));
        color: var(--warning-color);
    }
    
    .alert-info {
        background: color-mix(in srgb, var(--primary-color) 10%, var(--bg-primary));
        border: 1px solid color-mix(in srgb, var(--primary-color) 30%, var(--bg-primary));
        color: var(--primary-color);
    }
    
    .alert-success:hover, .alert-warning:hover, .alert-info:hover {
        transform: translateX(5px);
        box-shadow: 0 4px 12px var(--shadow);
    }
    
    /* Fallback para navegadores sin color-mix */
    @supports not (color: color-mix(in srgb, red, blue)) {
        .alert-success { background: #d1fae5; border-color: #a7f3d0; }
        .alert-warning { background: #fef3c7; border-color: #fde68a; }
        .alert-info { background: #dbeafe; border-color: #bfdbfe; }
        
        [data-theme="dark"] .alert-success { background: #064e3b; border-color: #065f46; }
        [data-theme="dark"] .alert-warning { background: #451a03; border-color: #92400e; }
        [data-theme="dark"] .alert-info { background: #1e3a8a; border-color: #1e40af; }
    }
    
    /* Resumen de procesamiento con efectos */
    .processing-summary {
        background: var(--bg-accent);
        padding: 1.5rem;
        border-radius: 8px;
        border-left: 4px solid var(--primary-color);
        animation: fadeInUp 0.7s ease-out;
        transition: all 0.3s ease;
        position: relative;
        overflow: hidden;
    }
    
    .processing-summary::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 2px;
        background: linear-gradient(90deg, var(--primary-color), var(--success-color), var(--primary-color));
        background-size: 200% 100%;
        animation: shimmer 2s infinite;
    }
    
    .processing-summary:hover {
        transform: translateY(-3px);
        box-shadow: 0 8px 20px var(--shadow);
    }
    
    .processing-summary h4 {
        margin: 0 0 1rem 0;
        color: var(--primary-dark);
        transition: color 0.3s ease;
    }
    
    .processing-summary:hover h4 {
        color: var(--primary-color);
    }
    
    .processing-summary p {
        margin: 0.5rem 0;
        color: var(--text-primary);
        transition: all 0.3s ease;
    }
    
    .processing-summary:hover p {
        transform: translateX(5px);
    }
    
    /* Botones de Streamlit con efectos personalizados */
    .stButton > button {
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
        border-radius: 10px !important;
        border: 1px solid var(--border-color) !important;
        position: relative !important;
        overflow: hidden !important;
        background: var(--bg-primary) !important;
        color: var(--text-primary) !important;
        padding: 1.5rem !important;
        font-size: 1rem !important;
        font-weight: 600 !important;
        text-align: center !important;
        box-shadow: 0 2px 4px var(--shadow) !important;
        white-space: pre-line !important;
        line-height: 1.2 !important;
    }
    
    .stButton > button:hover {
        transform: translateY(-8px) scale(1.02) !important;
        box-shadow: 0 12px 25px var(--shadow) !important;
        border-color: var(--primary-color) !important;
    }
    
    .stButton > button:active {
        transform: translateY(-2px) scale(1.01) !important;
    }
    
    /* Estilos específicos para botones de métricas */
    .stButton > button:nth-child(1) {
        color: var(--success-color) !important;
    }
    
    .stButton > button:nth-child(2) {
        color: var(--primary-color) !important;
    }
    
    .stButton > button:nth-child(3) {
        color: var(--danger-color) !important;
    }
    
    .stButton > button:nth-child(4) {
        color: var(--warning-color) !important;
    }
    
    /* Efectos para elementos de carga de archivos */
    .stFileUploader {
        animation: fadeInUp 0.6s ease-out;
    }
    
    .stFileUploader:hover {
        transform: translateY(-2px);
        transition: transform 0.3s ease;
    }
    
    /* Efectos para áreas de texto */
    .stTextArea textarea {
        transition: all 0.3s ease !important;
        border-radius: 8px !important;
    }
    
    .stTextArea textarea:focus {
        transform: scale(1.01) !important;
        box-shadow: 0 4px 12px var(--shadow) !important;
    }
    
    /* Footer con animación */
    .footer {
        text-align: center;
        color: var(--text-secondary);
        padding: 1rem;
        animation: fadeInUp 1s ease-out;
        transition: color 0.3s ease;
    }
    
    .footer:hover {
        color: var(--text-primary);
    }
    
    /* Animaciones de entrada escalonadas para elementos */
    .stColumn:nth-child(1) .metric-container {
        animation-delay: 0.1s;
    }
    
    .stColumn:nth-child(2) .metric-container {
        animation-delay: 0.2s;
    }
    
    .stColumn:nth-child(3) .metric-container {
        animation-delay: 0.3s;
    }
    
    .stColumn:nth-child(4) .metric-container {
        animation-delay: 0.4s;
    }
    
    /* Efectos para tablas */
    .stDataFrame {
        animation: fadeInUp 0.8s ease-out;
        transition: all 0.3s ease;
    }
    
    .stDataFrame:hover {
        box-shadow: 0 4px 12px var(--shadow);
    }
    
    /* Ocultando botones invisibles de Streamlit */
    .stButton > button:empty {
        display: none !important;
        height: 0 !important;
        padding: 0 !important;
        margin: 0 !important;
        border: none !important;
    }
    
    /* Asegurando que las métricas mantengan el cursor pointer */
    .metric-container {
        cursor: pointer !important;
    }
    .metric-triggers{
    position: absolute !important;
    left: -99999px !important;
    top: 0 !important;
    width: 0 !important;
    height: 0 !important;
    margin: 0 !important;
    padding: 0 !important;
    overflow: hidden !important;
    opacity: 0 !important;
    pointer-events: none !important;
    }
    /* Cubre las distintas variantes de botones en Streamlit */
    .metric-triggers .stButton,
    .metric-triggers [data-testid="stButton"],
    .metric-triggers button{
    width: 0 !important;
    height: 0 !important;
    padding: 0 !important;
    margin: 0 !important;
    border: 0 !important;
    }

    </style>
    """, unsafe_allow_html=True)

def get_icon(name: str) -> str:
    """Iconos para la interfaz"""
    icons = {
        "upload": "📁",
        "process": "⚙️",
        "clean": "🧹",
        "download": "💾",
        "new": "🆕",
        "maintained": "🔄",
        "deleted": "❌",
        "modified": "✏️",
        "platform": "🖥️",
        "warning": "⚠️",
        "success": "✅",
        "info": "ℹ️",
        "chart": "📊",
        "compare": "🔍"
    }
    return icons.get(name, "")

def render_main_header():
    """Renderiza el header principal"""
    st.markdown("""
    <div class="main-header">
        <h1>🚗 Extractor de Comparendos</h1>
        <p>Sistema integral para procesamiento y análisis de comparendos de tráfico</p>
    </div>
    """, unsafe_allow_html=True)

def render_section_header(title: str):
    """Renderiza un header de sección"""
    st.markdown(f"""
    <div class="section-header">
        <h3>{title}</h3>
    </div>
    """, unsafe_allow_html=True)

def render_alert(message: str, alert_type: str = "info", icon: str = "info"):
    """Renderiza una alerta con estilo"""
    st.markdown(f"""
    <div class="alert-{alert_type}">
        {get_icon(icon)} {message}
    </div>
    """, unsafe_allow_html=True)


import streamlit as st

def render_metric_cards(counts: dict, df_modificados):
    """Tarjetas + selector y botón 'Ver detalles' (sin cambiar el diseño de las tarjetas)."""
    modificados_count = len(df_modificados) if not df_modificados.empty else 0

    # ---- Tarjetas (solo visual) ----
    k1, k2, k3, k4 = st.columns(4)

    def card(value: int, label_text: str, extra_class: str):
        st.markdown(
            f"""
            <div class="metric-container">
                <div class="metric-value {extra_class}">{value}</div>
                <div class="metric-label">{label_text}</div>
            </div>
            """,
            unsafe_allow_html=True
        )

    with k1:
        card(counts.get("nuevos", 0), "🆕 NUEVOS", "metric-nuevos")
    with k2:
        card(counts.get("mantenidos", 0), "🔄 MANTENIDOS", "metric-mantenidos")
    with k3:
        card(counts.get("eliminados", 0), "❌ ELIMINADOS", "metric-eliminados")
    with k4:
        card(modificados_count, "✏️ MODIFICADOS", "metric-modificados")

    # ---- Selector + botón "Ver detalles" ----
    st.markdown("")  # pequeño espacio
    c1, c2, c3 = st.columns([1, 2, 1])
    with c2:
        opciones_map = {
            "🆕 Nuevos": "nuevos",
            "🔄 Mantenidos": "mantenidos",
            "❌ Eliminados": "eliminados",
            "✏️ Modificados": "modificados",
        }
        elegido = st.radio(
            "Elegir detalle",
            list(opciones_map.keys()),
            horizontal=True,
            label_visibility="collapsed",
        )

        if st.button("Ver detalles", use_container_width=True, type="primary"):
            st.session_state["comparendos_app_state"]["view_mode"] = opciones_map[elegido]
            # No hace falta st.rerun(): al estar dentro del mismo ciclo de render,
            # la parte inferior de app.py leerá view_mode y pintará la tabla.


def render_processing_summary(total_comparendos: int, total_plataformas: int, timestamp: str):
    """Renderiza el resumen de procesamiento"""
    st.markdown(f"""
    <div class="processing-summary">
        <h4>📋 Resumen de Procesamiento</h4>
        <p><strong>Total de comparendos:</strong> {total_comparendos}</p>
        <p><strong>Plataformas activas:</strong> {total_plataformas}</p>
        <p><strong>Última actualización:</strong> {timestamp}</p>
    </div>
    """, unsafe_allow_html=True)

def render_footer():
    """Renderiza el footer"""
    st.markdown("""
    <div class="footer">
        <p>🚗 Sistema de Extracción de Comparendos | Desarrollado con Streamlit</p>
    </div>
    """, unsafe_allow_html=True)
