import streamlit as st
import pandas as pd
import tempfile
from fpdf import FPDF
from PIL import Image
import os
from datetime import datetime

# Configuracao visual da pagina
st.set_page_config(page_title="RDO Digital - Minerva", layout="wide", page_icon="🏗️")

# Nome do arquivo que vai guardar os dados (Banco de Dados local)
ARQUIVO_EXCEL = "Banco_Dados_Obra_Minerva.xlsx"

# Funcao para salvar os dados nas abas do Excel sem apagar os anteriores
def salvar_dados(nova_linha_df, nome_aba):
    if os.path.exists(ARQUIVO_EXCEL):
        with pd.ExcelFile(ARQUIVO_EXCEL) as xls:
            abas_existentes = {sheet: pd.read_excel(xls, sheet) for sheet in xls.sheet_names}
    else:
        abas_existentes = {}

    if nome_aba in abas_existentes:
        abas_existentes[nome_aba] = pd.concat([abas_existentes[nome_aba], nova_linha_df], ignore_index=True)
    else:
        abas_existentes[nome_aba] = nova_linha_df

    with pd.ExcelWriter(ARQUIVO_EXCEL, engine='openpyxl') as writer:
        for sheet, df in abas_existentes.items():
            df.to_excel(writer, sheet_name=sheet, index=False)

# Funcao para ler os dados salvos
def carregar_dados(nome_aba):
    if os.path.exists(ARQUIVO_EXCEL):
        with pd.ExcelFile(ARQUIVO_EXCEL) as xls:
            if nome_aba in xls.sheet_names:
                return pd.read_excel(xls, nome_aba)
    return pd.DataFrame()

# --- CABECALHO DO SISTEMA ---
st.title("🏗️ RDO Digital/Gestão de Campo")
st.markdown("*Obra:* Jardins de Nazaré | *Construtora Minerva* | Engenharia 4.0")
st.divider()

# --- MENU DE ABAS ---
aba1, aba2, aba3, aba4, aba5 = st.tabs([
    "📋 RDO/Clima", 
    "👷 Equipes/Apartamentos", 
    "🚛 Concretagem", 
    "📌 RNC(Qualidade)",
    "📊 Painel do Coordenador"
])

# ==========================================
# ABA 1: RDO DIÁRIO E CLIMA REAL
# ==========================================
with aba1:
    st.subheader("Registro Diário de Obra")
    col1, col2, col3 = st.columns(3)
    with col1:
        data_rdo = st.date_input("Data", datetime.today())
    with col2:
        clima_m = st.selectbox("Clima Manhã (Real)", ["Bom / Sol", "Nublado", "Chuva Fraca", "Chuva Forte"])
    with col3:
        clima_t = st.selectbox("Clima Tarde (Real)", ["Bom / Sol", "Nublado", "Chuva Fraca", "Chuva Forte"])

    condicao = st.radio("Condição de Trabalho no Canteiro", ["Praticável", "Parcialmente Impraticável", "Totalmente Impraticável"], horizontal=True)

    horas_chuva = 0.0
    if "Chuva" in clima_m or "Chuva" in clima_t:
        horas_chuva = st.number_input("Quantas horas a obra ficou parada por chuva?", min_value=0.0, max_value=12.0, step=0.5)

    empresas = st.multiselect("Empresas / Visitas Técnicas Presentes", [
        "Equipe Própria Minerva", 
        "Cerqueira (Empreiteira)", 
        "Saint-Gobain (Monocapa)", 
        "Fiscalização / Prefeitura",
        "Outros Fornecedores"
    ])
    obs_visitas = st.text_input("Detalhes das visitas (Ex: Técnico da Saint-Gobain validou fachada norte)")
    atividades = st.text_area("Resumo das Atividades Executadas Hoje")

    if st.button("Salvar RDO do Dia", type="primary"):
        df_rdo = pd.DataFrame([{
            "Data": data_rdo.strftime("%d/%m/%Y"),
            "Clima_Manha": clima_m,
            "Clima_Tarde": clima_t,
            "Condicao": condicao,
            "Horas_Paradas": horas_chuva,
            "Terceiros": ", ".join(empresas),
            "Obs_Visitas": obs_visitas,
            "Atividades": atividades
        }])
        salvar_dados(df_rdo, "RDO_Diario")
        st.success("✅ RDO salvo com sucesso no banco de dados da obra!")

# ==========================================
# ABA 2: ALOCAÇÃO DE EQUIPES POR APARTAMENTO
# ==========================================
with aba2:
    st.subheader("Rastreabilidade de Equipes por Pavimento/Unidade")
    c1, c2, c3 = st.columns(3)
    with c1:
        colab = st.text_input("Nome do Colaborador ou Líder de Equipe")
        emp_colab = st.selectbox("Empresa", ["Construtora Minerva", "Cerqueira", "Saint-Gobain", "Outra"])
    with c2:
        pav = st.selectbox("Pavimento", ["Subsolo", "Térreo", "1º Pavimento", "2º Pavimento", "3º Pavimento", "4º Pavimento", "5º Pavimento","6º Pavimento", "7º Pavimento", "8º Pavimento", "9º Pavimento", "Cobertura", "Fachada"])
        apto = st.text_input("Apartamento ou Local (Ex: Apto 102, Hall)")
    with c3:
        serv = st.selectbox("Serviço Executado", ["Alvenaria", "Monocapa", "Contrapiso", "Hidráulica", "Elétrica", "Impermeabilização","Gesso", "Drywall", "Carpintaria","Pintura"])
        status_serv = st.selectbox("Status", ["Iniciado", "Em Andamento", "Concluído"])

    if st.button("Registrar Alocação de Equipe"):
        df_eq = pd.DataFrame([{
            "Data": datetime.today().strftime("%d/%m/%Y"),
            "Colaborador": colab,
            "Empresa": emp_colab,
            "Pavimento": pav,
            "Unidade": apto,
            "Servico": serv,
            "Status": status_serv
        }])
        salvar_dados(df_eq, "Alocacao_Equipes")
        st.success(f"✅ {colab} registrado no {pav} ({apto})!")

# ==========================================
# ABA 3: CONTROLE DE CONCRETAGEM
# ==========================================
with aba3:
    st.subheader("Recebimento de Concreto Usinado")
    cc1, cc2, cc3 = st.columns(3)
    with cc1:
        concreteira = st.text_input("Concreteira (Ex: Polimix, Votorantim)")
        nf = st.text_input("Número da Nota Fiscal / Ticket")
    with cc2:
        peca = st.text_input("Peça Concretada (Ex: Pilares 2º Pav)")
        fck = st.selectbox("FCK de Projeto (MPa)", [20, 25, 30, 35, 40])
    with cc3:
        vol_m3 = st.number_input("Volume (m³)", min_value=0.5, step=0.5)
        slump = st.number_input("Slump Obtido na Obra (cm)", min_value=1, max_value=30, value=12)

    status_conc = st.radio("Status do Recebimento", ["Aprovado", "Aprovado com Aditivo", "Recusado"], horizontal=True)

    if st.button("Salvar Caminhão de Concreto"):
        df_conc = pd.DataFrame([{
            "Data": datetime.today().strftime("%d/%m/%Y"),
            "Concreteira": concreteira,
            "NF": nf,
            "Peca": peca,
            "FCK": fck,
            "Volume_m3": vol_m3,
            "Slump_cm": slump,
            "Status": status_conc
        }])
        salvar_dados(df_conc, "Concretagem")
        st.success(f"✅ Caminhão NF {nf} ({vol_m3} m³) registrado!")

# ==========================================
# ABA 4: RNC ISSUES (CONTROLE DE QUALIDADE)
# ==========================================
with aba4:
    st.subheader("Apontamento de Pendências (Estilo BIM 360)")
    ci1, ci2 = st.columns(2)
    with ci1:
        local_issue = st.text_input("Local da Pendência (Ex: Pilar P14 - Térreo)")
        disc_issue = st.selectbox("Disciplina", ["Estrutura", "Alvenaria", "Monocapa / Fachada", "Instalações","Drywall", "Carpintaria""Contrapiso", "Segurança do Trabalho"])
    with ci2:
        resp_issue = st.selectbox("Responsável pela Correção", ["Mestre de Obras", "Cerqueira", "Saint-Gobain", "Equipe Minerva"])
        prazo_issue = st.date_input("Prazo Limite para Correção")

    desc_issue = st.text_area("Descrição detalhada do problema")

    if st.button("Abrir RNC Issue de Qualidade"):
        df_iss = pd.DataFrame([{
            "Data_Abertura": datetime.today().strftime("%d/%m/%Y"),
            "Local": local_issue,
            "Disciplina": disc_issue,
            "Descricao": desc_issue,
            "Responsavel": resp_issue,
            "Prazo": prazo_issue.strftime("%d/%m/%Y"),
            "Status": "Aberto"
        }])
        salvar_dados(df_iss, "Issues")
        st.warning(f"📌 Issue aberta e atribuída para: {resp_issue}")

# ==========================================
# ABA 5: PAINEL DO COORDENADOR (VISUALIZAÇÃO)
# ==========================================
with aba5:
    st.subheader("📊 Visão Gerencial em Tempo Real")
    st.info("Aqui o Coordenador acompanha todos os registros lançados na obra e pode baixar a planilha completa.")
    tab_v1, tab_v2, tab_v3, tab_v4 = st.tabs(["Histórico RDO", "Mapa de Equipes", "Concretagem", "RNCs Abertas"])

    # Função auxiliar para exibir tabela editável e salvar alterações
    def exibir_tabela_editavel(nome_aba, chave_unica):
        df_atual = carregar_dados(nome_aba)
        if not df_atual.empty:
            st.caption("💡 Dê um clique duplo em qualquer célula abaixo para editar o texto e depois clique em Salvar.")
            df_editado = st.data_editor(df_atual, use_container_width=True, key=chave_unica)
            
            if st.button(f"💾 Salvar alterações em {nome_aba}", key=f"btn_{chave_unica}"):
                with pd.ExcelWriter(ARQUIVO_EXCEL, engine="openpyxl", mode="a", if_sheet_exists="replace") as writer:
                    df_editado.to_excel(writer, sheet_name=nome_aba, index=False)
                st.success("Alterações salvas com sucesso!")
                st.rerun()
        else:
            st.info("Nenhum registro cadastrado nesta aba ainda.")

    with tab_v1:
        exibir_tabela_editavel("RDO_Diario", "edit_rdo")
    with tab_v2:
        exibir_tabela_editavel("Alocacao_Equipes", "edit_equipes")
    with tab_v3:
        df_c = carregar_dados("Concretagem")
        if not df_c.empty and "Volume_m3" in df_c.columns:
            st.metric("Volume Total Concretado (m³)", f"{df_c['Volume_m3'].sum():.2f} m³")
        exibir_tabela_editavel("Concretagem", "edit_concreto")
    with tab_v4:
        exibir_tabela_editavel("Issues", "edit_issues")
    
    st.divider()
    st.subheader("Excluir Registro")

    # Permite escolher de qual aba da planilha você quer apagar um registro
    aba_escolhida = st.selectbox(
        "Escolha a categoria do registro:",
        ["RDO_Diario", "Alocacao_Equipes", "Concretagem", "Issues"]
    )

    df_exclusao = carregar_dados(aba_escolhida)

    if not df_exclusao.empty:
        # Mostra o número da linha e as duas primeiras colunas para facilitar a identificação
        opcoes = [f"Linha {i} | {row.iloc[0]} - {row.iloc[1]}" for i, row in df_exclusao.iterrows()]
        selecionado = st.selectbox("Selecione o registro para apagar:", opcoes)

        if st.button("Excluir Registro Selecionado", type="primary"):
            indice = int(selecionado.split(" ")[1])
            df_exclusao = df_exclusao.drop(indice)

            # Salva a aba alterada sem apagar as outras abas do Excel
            with pd.ExcelWriter(ARQUIVO_EXCEL, engine="openpyxl", mode="a", if_sheet_exists="replace") as writer:
                df_exclusao.to_excel(writer, sheet_name=aba_escolhida, index=False)

            st.success("Registro excluído com sucesso!")
            st.rerun()
    else:
        st.info("Nenhum registro cadastrado nesta categoria.")
    # --- FIM DO BLOCO DE EXCLUSÃO ---
    # Botao para baixar o Excel completo
    if os.path.exists(ARQUIVO_EXCEL):
        with open(ARQUIVO_EXCEL, "rb") as file:
            st.download_button(
                label="📥 Baixar Planilha Completa da Obra (Excel)",
                data=file,
                file_name="Relatorio_Geral_Jardins_de_Nazare.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
            # --- INÍCIO DO GERADOR DE PDF COM FOTOS ---
    st.divider()
    st.subheader("📄 Gerar Relatório Diário em PDF")

    # 1. Campo para anexar várias fotos do celular ou computador
    fotos_enviadas = st.file_uploader(
        "Anexar fotos do serviço executado (JPG ou PNG):",
        type=["jpg", "jpeg", "png"],
        accept_multiple_files=True
    )

    # 2. Função que desenha o PDF
    def criar_pdf_rdo(df_dados, lista_fotos):
        pdf = FPDF()
        pdf.add_page()
        
        # Cabeçalho do Relatório
        pdf.set_font("Arial", "B", 16)
        pdf.cell(0, 10, "RELATORIO DIARIO DE OBRA (RDO) - MINERVA", ln=True, align="C")
        pdf.ln(5)

        # Pega o último RDO lançado na planilha
        if not df_dados.empty:
            ultimo_rdo = df_dados.iloc[-1]
            pdf.set_font("Arial", size=11)
            
            for coluna, valor in ultimo_rdo.items():
                # Limpa caracteres especiais para evitar erro de acentuação no PDF
                texto = f"{coluna}: {valor}".encode("latin-1", "replace").decode("latin-1")
                pdf.multi_cell(0, 8, texto)
                pdf.ln(1)
        else:
            pdf.set_font("Arial", size=11)
            pdf.cell(0, 10, "Nenhum dado de RDO registrado na planilha ainda.", ln=True)

        # Seção de Fotos Anexadas
        if lista_fotos:
            pdf.ln(5)
            pdf.set_font("Arial", "B", 13)
            pdf.cell(0, 10, "REGISTRO FOTOGRAFICO DE CAMPO:", ln=True)
            pdf.ln(3)

            for foto in lista_fotos:
                # Salva a foto temporariamente para o FPDF conseguir ler
                img = Image.open(foto)
                if img.mode in ("RGBA", "P"):
                    img = img.convert("RGB")
                
                with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp:
                    img.save(tmp.name, format="JPEG")
                    # Verifica se cabe na página atual, senão cria nova página
                    if pdf.get_y() > 190:
                        pdf.add_page()
                    pdf.image(tmp.name, x=15, w=120)
                    pdf.ln(5)
                os.unlink(tmp.name)

        return bytes(pdf.output())

    # 3. Botão para gerar e baixar o PDF
    if st.button("Preparar PDF do Último RDO"):
        df_rdo_atual = carregar_dados("RDO_Diario")
        pdf_pronto = criar_pdf_rdo(df_rdo_atual, fotos_enviadas)
        
        st.success("PDF gerado com sucesso! Clique abaixo para baixar.")
        st.download_button(
            label="📥 Baixar Relatório RDO em PDF",
            data=pdf_pronto,
            file_name="RDO_Minerva_Jardins.pdf",
            mime="application/pdf"
        )
    # --- FIM DO GERADOR DE PDF COM FOTOS ---