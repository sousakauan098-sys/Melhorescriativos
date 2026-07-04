import streamlit as st
import os
from openai import OpenAI
from PIL import Image
import io
import base64
import requests

# Configuração da página
st.set_page_config(
    page_title="Melhores Criativos",
    page_icon="🎨",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Título e descrição
st.title("🎨 Melhores Criativos")
st.markdown("### Ferramenta de IA para Criativos Publicitários de Alta Conversão")

# Inicializar cliente OpenAI
client = None
api_key = os.getenv("OPENAI_API_KEY")
if api_key:
    client = OpenAI(api_key=api_key)
else:
    st.error("Chave da API OpenAI não encontrada. Defina a variável de ambiente `OPENAI_API_KEY`.")

# Sidebar
with st.sidebar:
    st.header("Configurações")
    
    # Seleção de Modo
    mode = st.radio(
        "Modo de Operação",
        ["Melhoria", "Do Zero"],
        help="Escolha como deseja criar ou aprimorar seu criativo"
    )
    
    # Seleção de Formato
    aspect_ratio = st.selectbox(
        "Formato do Criativo",
        ["1:1 (Quadrado)", "9:16 (Stories/Reels)", "4:5 (Instagram Feed)", "16:9 (Horizontal)"],
        index=0
    )
    
    # Mapear para tamanhos DALL-E 3
    size_map = {
        "1:1 (Quadrado)": "1024x1024",
        "9:16 (Stories/Reels)": "1024x1792",
        "4:5 (Instagram Feed)": "1024x1280",
        "16:9 (Horizontal)": "1792x1024"
    }
    dalle_size = size_map[aspect_ratio]
    
    st.divider()
    st.caption("Powered by GPT-4o + DALL·E 3")

# Funções auxiliares
def image_to_base64(image):
    buffered = io.BytesIO()
    image.save(buffered, format="PNG")
    return base64.b64encode(buffered.getvalue()).decode('utf-8')

def enhance_prompt(base_prompt):
    enhancements = """
    High-resolution commercial photography, professional studio lighting, vibrant colors, 
    clean composition, high contrast, modern aesthetic, optimized for social media advertising, 
    attention-grabbing, high conversion potential, detailed textures, cinematic feel, 8k quality.
    """
    return f"{base_prompt}. {enhancements.strip()}"

# Inicializar session state
if 'generated_image' not in st.session_state:
    st.session_state.generated_image = None
if 'analysis' not in st.session_state:
    st.session_state.analysis = None

# ====================== INTERFACE PRINCIPAL ======================

if mode == "Melhoria":
    st.header("🔄 Modo Melhoria")
    st.markdown("Faça upload da **Imagem de Referência** e do **Criativo Atual**.")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Imagem de Referência")
        ref_image = st.file_uploader(
            "Arraste ou selecione a imagem de referência",
            type=["png", "jpg", "jpeg"],
            key="ref_uploader"
        )
        if ref_image:
            ref_pil = Image.open(ref_image)
            st.image(ref_pil, caption="Referência", use_column_width=True)
    
    with col2:
        st.subheader("Criativo Atual")
        current_image = st.file_uploader(
            "Arraste ou selecione o criativo atual",
            type=["png", "jpg", "jpeg"],
            key="current_uploader"
        )
        if current_image:
            current_pil = Image.open(current_image)
            st.image(current_pil, caption="Criativo Atual", use_column_width=True)
    
    if st.button("🔍 Analisar e Gerar Melhoria", type="primary", use_container_width=True):
        if not ref_image or not current_image:
            st.error("Por favor, faça upload de ambas as imagens.")
        elif not client:
            st.error("Cliente OpenAI não configurado.")
        else:
            with st.spinner("Analisando imagens com GPT-4o e gerando melhoria..."):
                try:
                    ref_pil = Image.open(ref_image)
                    current_pil = Image.open(current_image)
                    
                    ref_base64 = image_to_base64(ref_pil)
                    current_base64 = image_to_base64(current_pil)
                    
                    # Análise com Visão
                    analysis_response = client.chat.completions.create(
                        model="gpt-4o",
                        messages=[
                            {
                                "role": "system",
                                "content": "Você é um diretor de arte especializado em criativos de alta conversão para e-commerce e tráfego pago."
                            },
                            {
                                "role": "user",
                                "content": [
                                    {"type": "text", "text": "Analise o que falta no criativo atual comparado à referência (estética, cores, iluminação, composição, hierarquia visual). Sugira melhorias precisas."},
                                    {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{ref_base64}"}},
                                    {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{current_base64}"}},
                                ]
                            }
                        ],
                        max_tokens=600
                    )
                    
                    analysis = analysis_response.choices[0].message.content
                    st.session_state.analysis = analysis
                    
                    # Geração com DALL-E 3
                    improved_prompt = f"Crie uma versão aprimorada seguindo exatamente estas orientações: {analysis}"
                    
                    response = client.images.generate(
                        model="dall-e-3",
                        prompt=enhance_prompt(improved_prompt),
                        size=dalle_size,
                        quality="hd",
                        n=1
                    )
                    
                    st.session_state.generated_image = response.data[0].url
                    st.success("✅ Criativo aprimorado gerado com sucesso!")
                    
                except Exception as e:
                    st.error(f"Erro: {str(e)}")

else:  # Modo Do Zero
    st.header("✨ Modo Criação do Zero")
    st.markdown("Descreva o criativo que deseja gerar.")
    
    user_prompt = st.text_area(
        "Prompt detalhado",
        placeholder="Ex: Produto de suplemento em embalagem preta premium flutuando com fundo gradiente roxo e dourado, iluminação dramática, estilo luxuoso...",
        height=180
    )
    
    if st.button("🚀 Gerar Criativo", type="primary", use_container_width=True):
        if not user_prompt.strip():
            st.error("Insira um prompt.")
        elif not client:
            st.error("Cliente OpenAI não configurado.")
        else:
            with st.spinner("Gerando criativo com DALL·E 3..."):
                try:
                    response = client.images.generate(
                        model="dall-e-3",
                        prompt=enhance_prompt(user_prompt),
                        size=dalle_size,
                        quality="hd",
                        n=1
                    )
                    st.session_state.generated_image = response.data[0].url
                    st.success("✅ Criativo gerado com sucesso!")
                except Exception as e:
                    st.error(f"Erro: {str(e)}")

# ====================== ÁREA DE RESULTADO ======================
if st.session_state.generated_image:
    st.divider()
    st.header("🎉 Seu Criativo Final")
    st.image(st.session_state.generated_image, caption="Imagem gerada pela IA", use_column_width=True)
    
    # Download
    try:
        img_data = requests.get(st.session_state.generated_image).content
        st.download_button(
            label="📥 Baixar Imagem em Alta Qualidade",
            data=img_data,
            file_name="criativo_melhorescriativos.png",
            mime="image/png",
            use_container_width=True
        )
    except:
        st.info("Clique com o botão direito na imagem acima → Salvar imagem como...")

if st.session_state.analysis and mode == "Melhoria":
    with st.expander("📋 Análise Detalhada da IA (GPT-4o)"):
        st.markdown(st.session_state.analysis)

st.divider()
st.caption("Melhores Criativos © 2026 • Desenvolvido com Streamlit + OpenAI")
