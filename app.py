import streamlit as st
import spacy
from spacy import displacy
import pandas as pd
import io
from pypdf import PdfReader

# 1. Configuração da Página
st.set_page_config(
    page_title="Extrator de Entidades (NER)",
    page_icon="🏷️",
    layout="centered"
)

# 2. Inicialização do Modelo spaCy em Português de Alta Precisão (com Cache)
@st.cache_resource
def carregar_modelo_ner():
    # Mudamos para pt_core_news_lg para garantir precisão máxima e alinhar com o Render
    return spacy.load("pt_core_news_lg")

nlp = carregar_modelo_ner()

TRADUCAO_ENTIDADES = {
    "PER": "Pessoa",
    "ORG": "Empresa / Organização",
    "LOC": "Local / Lugar",
    "MISC": "Outros (Miscelânea)"
}

# 3. Interface do Usuário
st.title("🏷️ Extrator de Entidades Nomeadas (NER)")
st.write("Identifique automaticamente Pessoas, Empresas e Locais em seus documentos.")

# Seletor de método de entrada
metodo_entrada = st.radio(
    "Escolha o método de entrada dos dados:",
    ["✍️ Digitar Texto", "📁 Upload de Arquivo"],
    horizontal=True
)

# Inicializa a variável vazia
texto_para_analise = ""

if metodo_entrada == "✍️ Digitar Texto":
    texto_puro = st.text_area(
        "Cole ou digite seu texto aqui:", 
        placeholder="Ex: O empresário Elon Musk visitou a sede da Petrobras no Rio de Janeiro.",
        height=150
    )
    if texto_puro:
        texto_para_analise = texto_puro

else:
    arquivo_carregado = st.file_uploader("Escolha um arquivo .txt ou .pdf", type=["txt", "pdf"])
    if arquivo_carregado is not None:
        nome_arquivo = arquivo_carregado.name
        
        if nome_arquivo.endswith('.txt'):
            texto_para_analise = arquivo_carregado.read().decode("utf-8")
        
        elif nome_arquivo.endswith('.pdf'):
            leitor_pdf = PdfReader(arquivo_carregado)
            texto_pdf_limpo = "" 
            for pagina in leitor_pdf.pages:
                texto_pag = pagina.extract_text()
                if texto_pag:
                    texto_pdf_limpo += texto_pag + "\n"
            texto_para_analise = texto_pdf_limpo
            
        st.success(f"Arquivo '{nome_arquivo}' pronto para análise!")

# =========================================================================
# 4. Botão de Disparo Fixo na Tela
# =========================================================================
st.markdown("---")
if st.button("Iniciar Extração de Entidades (NER)", type="primary", use_container_width=True):
    
    if not texto_para_analise.strip():
        st.warning("⚠️ O sistema não detectou nenhum conteúdo. Por favor, digite um texto ou faça o upload de um arquivo primeiro!")
    
    else:
        with st.spinner("O spaCy de Alta Precisão está escaneando o documento atual..."):
            # Executa o NER de alta precisão
            doc = nlp(texto_para_analise)
            
            # --- VISUALIZAÇÃO GRÁFICA (Displacy) ---
            st.subheader("🔍 Entidades Destacadas no Texto")
            html_displacy = displacy.render(doc, style="ent", page=False)
            st.components.v1.html(html_displacy, height=250, scrolling=True)
            
            # --- CONSTRUÇÃO DA TABELA DE DADOS ---
            dados_entidades = []
            for ent in doc.ents:
                # Filtro inteligente: ignora ruídos analíticos de 1 letra ou termos fantasmas conhecidos
                if len(ent.text.strip()) <= 1 or ent.text.strip().lower() in ["system", "super annoying"]:
                    continue
                    
                tipo_traduzido = TRADUCAO_ENTIDADES.get(ent.label_, ent.label_)
                dados_entidades.append({
                    "Entidade Encontrada": ent.text,
                    "Tipo de Entidade": tipo_traduzido,
                    "Posição Inicial": ent.start_char,
                    "Posição Final": ent.end_char
                })
            
            st.markdown("---")
            st.subheader("📊 Tabela Resumo das Entidades")
            
            if dados_entidades:
                df_entidades = pd.DataFrame(dados_entidades)
                df_limpo = df_entidades.drop_duplicates(subset=["Entidade Encontrada", "Tipo de Entidade"])
                st.dataframe(df_limpo, use_container_width=True)
                
                # Criar botão para download em Excel
                buffer_excel = io.BytesIO()
                with pd.ExcelWriter(buffer_excel, engine='openpyxl') as writer:
                    df_limpo.to_excel(writer, index=False, sheet_name='Entidades_Extraidas')
                
                st.download_button(
                    label="📥 Baixar Relatório de Entidades (.xlsx)",
                    data=buffer_excel.getvalue(),
                    file_name="relatorio_entidades_ner.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
            else:
                st.info("Nenhuma entidade (Pessoas, Empresas ou Lugares) foi detectada no documento atual.")