# Arquivo: app/main.py
import streamlit as st

# CONFIGURAÇÃO DA PÁGINA DEVE SER O PRIMEIRO COMANDO STREAMLIT
st.set_page_config(
    page_title="⚽ Simulador de Futebol Completo",
    page_icon="⚽",
    layout="wide",
    initial_sidebar_state="expanded",
)

import pandas as pd
import os
import sys
import re

# Adiciona o diretório raiz ao sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Importar os módulos da aplicação
from utils.io import carregar_clubes, carregar_jogadores, carregar_historico, filtrar_historico_por_time
from app.simulacao import simular_partida
from app.estatisticas import exibir_estatisticas_time
from app.classificacao import gerar_tabela_classificacao, gerar_tabela_artilharia, exibir_classificacao_com_logos

# NOVA IMPORTAÇÃO PARA TORNEIOS
try:
    from app.torneios import pagina_torneios, exibir_classificacao_geral_torneios
    TORNEIOS_DISPONIVEL = True
except ImportError:
    TORNEIOS_DISPONIVEL = False

# NOVA IMPORTAÇÃO PARA LIGAS
try:
    from app.ligas import pagina_ligas, exibir_hall_da_fama_ligas, carregar_historico_ligas
    LIGAS_DISPONIVEL = True
except ImportError as e:
    LIGAS_DISPONIVEL = False
    # Não mostrar erro durante import - será mostrado na sidebar depois

def processar_marcadores_gols(marcadores_gols_str):
    """
    Processa a string de marcadores_gols e retorna lista de artilheiros formatada.
    Formato esperado: "Nome:Minuto:Time;Nome:Minuto:Time"
    Retorna: ["Nome (Time)", "Nome (Time)"]
    """
    if not marcadores_gols_str or pd.isna(marcadores_gols_str) or str(marcadores_gols_str).strip() == '':
        return []
    
    try:
        artilheiros = []
        # Dividir por ponto e vírgula
        marcadores = str(marcadores_gols_str).split(';')
        
        for marcador in marcadores:
            if ':' in marcador:
                # Formato: Nome:Minuto:Time
                partes = marcador.split(':')
                if len(partes) >= 3:
                    nome = partes[0].strip()
                    time = partes[2].strip()
                    artilheiros.append(f"{nome} ({time})")
        
        return artilheiros
    except:
        return []

def extrair_artilheiros_para_contagem(historico):
    """
    Extrai todos os artilheiros do histórico para contagem de gols.
    Compatível com ambos os formatos (marcadores_gols e artilheiros).
    """
    todos_artilheiros = []
    
    for _, partida in historico.iterrows():
        # Primeiro, tentar extrair dos marcadores_gols (formato correto)
        if 'marcadores_gols' in partida and pd.notna(partida['marcadores_gols']):
            artilheiros_marcadores = processar_marcadores_gols(partida['marcadores_gols'])
            todos_artilheiros.extend(artilheiros_marcadores)
        
        # Se não houver marcadores_gols ou estiver vazio, tentar artilheiros (formato antigo)
        elif 'artilheiros' in partida and pd.notna(partida['artilheiros']) and str(partida['artilheiros']).strip():
            artilheiros_str = str(partida['artilheiros'])
            if artilheiros_str != 'nan' and artilheiros_str.strip():
                # Dividir por vírgula
                artilheiros_lista = [art.strip() for art in artilheiros_str.split(',') if art.strip()]
                todos_artilheiros.extend(artilheiros_lista)
    
    return todos_artilheiros

def gerar_tabela_artilharia_corrigida(historico):
    """
    Gera tabela de artilharia usando o formato correto dos marcadores.
    """
    if historico is None or len(historico) == 0:
        return None
    
    # Extrair todos os artilheiros
    todos_artilheiros = extrair_artilheiros_para_contagem(historico)
    
    if not todos_artilheiros:
        return None
    
    # Contar gols por jogador
    contagem_gols = {}
    for artilheiro in todos_artilheiros:
        if artilheiro in contagem_gols:
            contagem_gols[artilheiro] += 1
        else:
            contagem_gols[artilheiro] = 1
    
    # Converter para DataFrame e ordenar
    artilheiros_df = pd.DataFrame(list(contagem_gols.items()), columns=['Jogador', 'Gols'])
    artilheiros_df = artilheiros_df.sort_values('Gols', ascending=False)
    artilheiros_df = artilheiros_df.reset_index(drop=True)
    
    return artilheiros_df

def main():
    """
    Função principal que inicia a aplicação Streamlit.
    """
    
    st.title("⚽ Simulador de Partidas de Futebol")
    
    # Carregar dados dos clubes e jogadores
    with st.spinner("🔄 Carregando dados..."):
        clubes = carregar_clubes()
        carregar_jogadores(clubes=clubes)
    
    # Exibir informações na sidebar
    st.sidebar.title("📊 Informações Gerais")
    
    # Verificar e exibir avisos sobre módulos não encontrados
    if not TORNEIOS_DISPONIVEL:
        st.sidebar.warning("⚠️ Módulo de torneios não encontrado. Crie o arquivo app/torneios.py")
    
    if not LIGAS_DISPONIVEL:
        st.sidebar.warning("⚠️ Módulo de ligas não encontrado. Crie o arquivo app/ligas.py")
    
    if clubes:
        st.sidebar.success(f"✅ {len(clubes)} clubes carregados")
        total_jogadores = sum(len(clube['jogadores']) for clube in clubes.values())
        st.sidebar.info(f"👥 {total_jogadores} jogadores no total")
    else:
        st.sidebar.error("❌ Erro ao carregar clubes")
    
    # Carregar histórico (compartilhado entre as abas)
    historico = carregar_historico()
    
    if historico is not None:
        st.sidebar.metric("⚽ Partidas Simuladas", len(historico))
    
    # Verificar se há torneios realizados
    try:
        import json
        arquivo_torneios = "data/torneios/historico_torneios.json"
        if os.path.exists(arquivo_torneios):
            with open(arquivo_torneios, 'r', encoding='utf-8') as f:
                historico_torneios = json.load(f)
            st.sidebar.metric("🏆 Torneios Realizados", len(historico_torneios))
        else:
            st.sidebar.metric("🏆 Torneios Realizados", 0)
    except:
        st.sidebar.metric("🏆 Torneios Realizados", 0)
    
    # Verificar se há ligas realizadas
    if LIGAS_DISPONIVEL:
        try:
            historico_ligas = carregar_historico_ligas()
            st.sidebar.metric("🏆 Ligas Realizadas", len(historico_ligas))
        except Exception as e:
            st.sidebar.metric("🏆 Ligas Realizadas", 0)
            st.sidebar.error(f"Erro ao carregar histórico de ligas: {str(e)[:50]}...")
    
    # CRIAR ABAS - AGORA COM LIGAS E CLASSIFICAÇÃO DE TORNEIOS
    abas = ["⚽ Simulador", "📊 Histórico", "🏆 Classificação"]
    
    if LIGAS_DISPONIVEL:
        abas.append("🏅 Ligas")
    
    if TORNEIOS_DISPONIVEL:
        abas.append("🏟️ Torneios")
    
    # Sempre adicionar Hall da Fama se houver pelo menos torneios ou ligas
    if TORNEIOS_DISPONIVEL or LIGAS_DISPONIVEL:
        abas.append("👑 Hall da Fama")
    
    # Criar as abas dinamicamente
    tabs = st.tabs(abas)
    
    # ABA 1: SIMULADOR
    with tabs[0]:
        st.header("Simulador de Partidas")
        
        if not clubes:
            st.error("❌ Nenhum clube carregado. Verifique os arquivos de dados.")
            return
        
        # Opções de clubes
        opcoes = [(cid, dados['nome']) for cid, dados in clubes.items()]
        
        # Container para exibir os times lado a lado
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("Selecione o time mandante:")
            clube1_id = st.selectbox(
                label="Time mandante",
                options=opcoes,
                format_func=lambda x: x[1],
                label_visibility="collapsed"
            )
            
            # Exibir logo grande do time selecionado
            if clubes[clube1_id[0]].get('logo_base64'):
                st.markdown(
                    f"""<div style="display: flex; justify-content: center; margin: 20px 0;">
                    <img src="data:image/png;base64,{clubes[clube1_id[0]]['logo_base64']}" 
                    style="max-width: 100px; max-height: 100px;">
                    </div>""",
                    unsafe_allow_html=True
                )
            st.markdown(f"<h3 style='text-align: center;'>{clubes[clube1_id[0]]['nome']}</h3>", unsafe_allow_html=True)
        
        with col2:
            st.write("Selecione o time visitante:")
            clube2_id = st.selectbox(
                label="Time visitante",
                options=opcoes,
                index=1 if len(opcoes) > 1 else 0,
                format_func=lambda x: x[1],
                label_visibility="collapsed"
            )
            
            # Exibir logo grande do time selecionado
            if clubes[clube2_id[0]].get('logo_base64'):
                st.markdown(
                    f"""<div style="display: flex; justify-content: center; margin: 20px 0;">
                    <img src="data:image/png;base64,{clubes[clube2_id[0]]['logo_base64']}" 
                    style="max-width: 100px; max-height: 100px;">
                    </div>""",
                    unsafe_allow_html=True
                )
            st.markdown(f"<h3 style='text-align: center;'>{clubes[clube2_id[0]]['nome']}</h3>", unsafe_allow_html=True)
        
        # Exibir o placar inicial do confronto
        st.markdown(
            f"""
            <div style="display: flex; align-items: center; justify-content: center; margin: 30px 0;">
                <div style="text-align: center;">
                    {"" if not clubes[clube1_id[0]].get('logo_base64') else f'<img src="data:image/png;base64,{clubes[clube1_id[0]]["logo_base64"]}" style="max-width: 60px; max-height: 60px;" alt="{clubes[clube1_id[0]]["nome"]}">'}
                </div>
                <div style="font-size: 32px; font-weight: bold; margin: 0 20px;">
                    VS
                </div>
                <div style="text-align: center;">
                    {"" if not clubes[clube2_id[0]].get('logo_base64') else f'<img src="data:image/png;base64,{clubes[clube2_id[0]]["logo_base64"]}" style="max-width: 60px; max-height: 60px;" alt="{clubes[clube2_id[0]]["nome"]}">'}
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

        if clube1_id[0] == clube2_id[0]:
            st.warning("⚠️ Selecione dois clubes diferentes para simular a partida.")
        else:
            # Centralizar o botão
            col1, col2, col3 = st.columns([1, 1, 1])
            with col2:
                if st.button("⚽ Simular Partida", use_container_width=True, type="primary"):
                    try:
                        simular_partida(clubes[clube1_id[0]], clubes[clube2_id[0]])
                    except Exception as e:
                        st.error(f"❌ Erro na simulação: {e}")
    
    # ABA 2: HISTÓRICO MELHORADO
    with tabs[1]:
        st.header("📊 Histórico e Estatísticas")
        
        if historico is None:
            st.info("📝 Não há partidas registradas ainda. Simule algumas partidas primeiro!")
        else:
            # Estatísticas rápidas no topo
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("⚽ Total de Partidas", len(historico))
            
            with col2:
                total_gols = historico['gols_casa'].sum() + historico['gols_visitante'].sum()
                st.metric("🥅 Total de Gols", total_gols)
            
            with col3:
                media_gols = total_gols / len(historico) if len(historico) > 0 else 0
                st.metric("📊 Média de Gols/Jogo", f"{media_gols:.1f}")
            
            with col4:
                empates = len(historico[historico['gols_casa'] == historico['gols_visitante']])
                st.metric("🤝 Empates", empates)
            
            st.markdown("---")
            
            # Obter lista de times para filtrar
            times = pd.concat([historico['time_casa'], historico['time_visitante']]).unique()
            time_selecionado = st.selectbox("🔍 Selecione um time para ver estatísticas:", 
                                          ["Todos os times"] + sorted(times.tolist()))
            
            if time_selecionado != "Todos os times":
                # Mostrar logo do time selecionado (se disponível)
                for clube_id, clube in clubes.items():
                    if clube['nome'] == time_selecionado and clube.get('logo_base64'):
                        st.markdown(
                            f"""<div style="display: flex; justify-content: center; margin: 20px 0;">
                            <img src="data:image/png;base64,{clube['logo_base64']}" 
                            style="max-width: 100px; max-height: 100px;">
                            </div>""",
                            unsafe_allow_html=True
                        )
                        break
                
                # Filtrar histórico pelo time selecionado
                historico_time = filtrar_historico_por_time(historico, time_selecionado)
                
                # Exibir estatísticas
                exibir_estatisticas_time(historico_time, time_selecionado)
            
            # Opção para ver todo o histórico
            if st.checkbox("📋 Ver histórico completo de todas as partidas"):
                st.subheader("📅 Histórico Completo")
                
                # Criar uma cópia do histórico para adicionar coluna de resultado
                historico_exibicao = historico.copy()
                
                # Adicionar coluna de resultado
                def determinar_resultado(row):
                    # Se já existe coluna vencedor, usar ela
                    if 'vencedor' in row and pd.notna(row['vencedor']) and row['vencedor'] != '':
                        if row['vencedor'] == 'Empate':
                            return "🤝 Empate"
                        else:
                            return f"🏆 {row['vencedor']}"
                    
                    # Caso contrário, calcular baseado nos gols
                    gols_casa = row['gols_casa']
                    gols_visitante = row['gols_visitante']
                    time_casa = row['time_casa']
                    time_visitante = row['time_visitante']
                    
                    if gols_casa > gols_visitante:
                        return f"🏆 {time_casa}"
                    elif gols_visitante > gols_casa:
                        return f"🏆 {time_visitante}"
                    else:
                        return "🤝 Empate"
                
                historico_exibicao['Resultado'] = historico_exibicao.apply(determinar_resultado, axis=1)
                
                # Determinar quais colunas mostrar baseado no que está disponível
                colunas_disponiveis = historico_exibicao.columns.tolist()
                colunas_para_mostrar = ['data', 'time_casa', 'gols_casa', 'gols_visitante', 'time_visitante', 'Resultado']
                
                # Adicionar colunas extras se disponíveis
                if 'marcadores_gols' in colunas_disponiveis:
                    colunas_para_mostrar.append('marcadores_gols')
                if 'artilheiros' in colunas_disponiveis:
                    colunas_para_mostrar.append('artilheiros')
                
                # Filtrar apenas colunas que existem
                colunas_finais = [col for col in colunas_para_mostrar if col in colunas_disponiveis]
                historico_exibicao = historico_exibicao[colunas_finais]
                
                # Renomear colunas para melhor apresentação
                nomes_colunas = {
                    'data': 'Data',
                    'time_casa': 'Time Casa',
                    'gols_casa': 'Gols Casa',
                    'gols_visitante': 'Gols Visitante', 
                    'time_visitante': 'Time Visitante',
                    'marcadores_gols': 'Placar',
                    'artilheiros': 'Artilheiros'
                }
                
                historico_exibicao = historico_exibicao.rename(columns=nomes_colunas)
                
                # Ordenar por data (mais recente primeiro)
                historico_exibicao = historico_exibicao.sort_values('Data', ascending=False)
                
                # Limitar a exibição para melhor performance
                limite = st.slider("Número de partidas a exibir:", 5, len(historico), min(50, len(historico)))
                
                # Opção de visualização
                tipo_visualizacao = st.radio(
                    "Tipo de visualização:",
                    ["📊 Tabela Simples", "🎨 Tabela Estilizada"],
                    horizontal=True
                )
                
                if tipo_visualizacao == "📊 Tabela Simples":
                    # Exibição simples com dataframe
                    st.dataframe(
                        historico_exibicao.head(limite).reset_index(drop=True),
                        hide_index=True,
                        use_container_width=True
                    )
                else:
                    # Exibição estilizada
                    st.markdown("### 🏆 Resultados das Partidas")
                    
                    partidas_exibir = historico_exibicao.head(limite)
                    historico_original = historico.sort_values('data', ascending=False)
                    
                    for idx, (_, partida) in enumerate(partidas_exibir.iterrows()):
                        # Obter dados originais correspondentes
                        partida_original = historico_original.iloc[idx]
                        gols_casa = partida_original['gols_casa']
                        gols_visitante = partida_original['gols_visitante']
                        
                        # Buscar logos dos times
                        logo_casa = ""
                        logo_visitante = ""
                        
                        for clube in clubes.values():
                            if clube['nome'] == partida['Time Casa'] and clube.get('logo_base64'):
                                logo_casa = f'<img src="data:image/png;base64,{clube["logo_base64"]}" style="width: 25px; height: 25px; margin-right: 5px; vertical-align: middle;">'
                            if clube['nome'] == partida['Time Visitante'] and clube.get('logo_base64'):
                                logo_visitante = f'<img src="data:image/png;base64,{clube["logo_base64"]}" style="width: 25px; height: 25px; margin-left: 5px; vertical-align: middle;">'
                        
                        # Determinar cor do placar
                        if gols_casa > gols_visitante:
                            cor_casa = "font-weight: bold; color: #28a745;"
                            cor_visitante = "color: #6c757d;"
                        elif gols_visitante > gols_casa:
                            cor_casa = "color: #6c757d;"
                            cor_visitante = "font-weight: bold; color: #28a745;"
                        else:
                            cor_casa = "font-weight: bold; color: #ffc107;"
                            cor_visitante = "font-weight: bold; color: #ffc107;"
                        
                        # Criar card da partida
                        st.markdown(
                            f"""
                            <div style="border: 1px solid #dee2e6; border-radius: 8px; padding: 15px; margin-bottom: 10px; background-color: #f8f9fa;">
                                <div style="display: flex; justify-content: space-between; align-items: center;">
                                    <div style="flex: 1; text-align: center;">
                                        <div style="display: flex; align-items: center; justify-content: center; margin-bottom: 5px;">
                                            {logo_casa}
                                            <span style="{cor_casa}">{partida['Time Casa']}</span>
                                        </div>
                                    </div>
                                    
                                    <div style="flex: 0 0 80px; text-align: center; font-size: 24px; font-weight: bold; margin: 0 20px;">
                                        <span style="{cor_casa}">{gols_casa}</span>
                                        <span style="color: #6c757d;"> × </span>
                                        <span style="{cor_visitante}">{gols_visitante}</span>
                                    </div>
                                    
                                    <div style="flex: 1; text-align: center;">
                                        <div style="display: flex; align-items: center; justify-content: center; margin-bottom: 5px;">
                                            <span style="{cor_visitante}">{partida['Time Visitante']}</span>
                                            {logo_visitante}
                                        </div>
                                    </div>
                                </div>
                                
                                <div style="text-align: center; margin-top: 10px; padding-top: 10px; border-top: 1px solid #dee2e6;">
                                    <small style="color: #6c757d;">
                                        📅 {partida['Data']} | {partida['Resultado']}
                                    </small>
                                </div>
                                
                                {f'<div style="text-align: center; margin-top: 5px;"><small style="color: #6c757d;">⚽ {partida["Artilheiros"]}</small></div>' if 'Artilheiros' in partida and partida['Artilheiros'] and str(partida['Artilheiros']).strip() and str(partida['Artilheiros']) != 'nan' else ''}
                            </div>
                            """,
                            unsafe_allow_html=True
                        )
                
                if limite < len(historico):
                    st.info(f"Exibindo {limite} de {len(historico)} partidas. Ajuste o slider para ver mais.")
    
    # ABA 3: CLASSIFICAÇÃO
    with tabs[2]:
        st.header("🏆 Classificação")
        
        if historico is None:
            st.info("📝 Não há partidas registradas ainda. Simule algumas partidas primeiro!")
        else:
            # Gerar a tabela de classificação
            tabela = gerar_tabela_classificacao(historico)
            
            # Exibir a tabela de classificação com logos
            if tabela is not None:
                # Usar a função melhorada para exibir a classificação
                exibir_classificacao_com_logos(tabela, clubes)
                
                st.markdown("---")
                
                # Seção de artilharia do campeonato
                artilheiros_df = gerar_tabela_artilharia_corrigida(historico)  # Usar função corrigida
                if artilheiros_df is not None:
                    st.subheader("🥇 Artilharia do Campeonato")
                    
                    # Exibe artilheiros formatados
                    for i, (jogador, gols) in enumerate(zip(artilheiros_df['Jogador'], artilheiros_df['Gols'])):
                        # Extrai o nome do time entre parênteses
                        match = re.search(r'\((.*?)\)', jogador)
                        if match:
                            nome_jogador = jogador.split('(')[0].strip()
                            time_nome = match.group(1)
                            
                            # Busca o logo do time
                            logo_html = ""
                            for cid, clube in clubes.items():
                                if clube['nome'] == time_nome and clube.get('logo_base64'):
                                    # Exibe o jogador com logo do time
                                    st.markdown(
                                        f"""<div style="display: flex; align-items: center; margin-bottom: 5px;">
                                           <div style="width: 25px; text-align: right; margin-right: 10px;"><b>{i+1}º</b></div>
                                           <img src="data:image/png;base64,{clube['logo_base64']}" 
                                                style="width: 20px; height: 20px; margin-right: 8px;">
                                           <div style="flex: 1;"><b>{nome_jogador}</b> ({time_nome})</div>
                                           <div style="width: 30px; text-align: right;"><b>{gols}</b> ⚽</div>
                                        </div>""",
                                        unsafe_allow_html=True
                                    )
                                    break
                            else:
                                # Se não encontrou logo, exibe sem logo
                                st.markdown(
                                    f"""<div style="display: flex; align-items: center; margin-bottom: 5px;">
                                       <div style="width: 25px; text-align: right; margin-right: 10px;"><b>{i+1}º</b></div>
                                       <div style="flex: 1; margin-left: 28px;"><b>{nome_jogador}</b> ({time_nome})</div>
                                       <div style="width: 30px; text-align: right;"><b>{gols}</b> ⚽</div>
                                    </div>""",
                                    unsafe_allow_html=True
                                )
                        else:
                            # Fallback se não conseguir extrair o time
                            st.markdown(f"**{i+1}º** {jogador} - **{gols}** ⚽")
                        
                        # Limite para os top 15 artilheiros
                        if i >= 14:
                            st.info(f"Exibindo os primeiros 15 de {len(artilheiros_df)} artilheiros")
                            break
    
    # ABA 4: LIGAS (se disponível)
    current_tab = 3
    if LIGAS_DISPONIVEL:
        with tabs[current_tab]:
            try:
                pagina_ligas(clubes)
            except Exception as e:
                st.error(f"❌ Erro ao carregar módulo de ligas: {e}")
                st.info("📝 Verifique se o arquivo app/ligas.py existe e está correto.")
        current_tab += 1
    
    # ABA 5: TORNEIOS (se disponível)
    if TORNEIOS_DISPONIVEL:
        with tabs[current_tab]:
            try:
                pagina_torneios(clubes)
            except Exception as e:
                st.error(f"❌ Erro ao carregar módulo de torneios: {e}")
                st.info("📝 Verifique se o arquivo app/torneios.py existe e está correto.")
        current_tab += 1
    
    # ABA 6: HALL DA FAMA (se houver torneios ou ligas)
    if TORNEIOS_DISPONIVEL or LIGAS_DISPONIVEL:
        with tabs[current_tab]:
            st.header("👑 Hall da Fama")
            
            # Criar sub-abas para diferentes tipos de competições
            subtabs = []
            if LIGAS_DISPONIVEL:
                subtabs.append("🏆 Ligas")
            if TORNEIOS_DISPONIVEL:
                subtabs.append("🏟️ Torneios")
            
            if len(subtabs) > 1:
                sub_tab_objects = st.tabs(subtabs)
                
                subtab_index = 0
                if LIGAS_DISPONIVEL:
                    with sub_tab_objects[subtab_index]:
                        try:
                            exibir_hall_da_fama_ligas(clubes)
                        except Exception as e:
                            st.error(f"❌ Erro ao carregar hall da fama de ligas: {e}")
                    subtab_index += 1
                
                if TORNEIOS_DISPONIVEL:
                    with sub_tab_objects[subtab_index]:
                        try:
                            exibir_classificacao_geral_torneios(clubes)
                        except Exception as e:
                            st.error(f"❌ Erro ao carregar hall da fama de torneios: {e}")
            else:
                # Se só há um tipo, exibir diretamente
                if LIGAS_DISPONIVEL:
                    try:
                        exibir_hall_da_fama_ligas(clubes)
                    except Exception as e:
                        st.error(f"❌ Erro ao carregar hall da fama de ligas: {e}")
                elif TORNEIOS_DISPONIVEL:
                    try:
                        exibir_classificacao_geral_torneios(clubes)
                    except Exception as e:
                        st.error(f"❌ Erro ao carregar hall da fama de torneios: {e}")
    
    # Rodapé com informações
    st.markdown("---")
    st.markdown("""
    <div style="text-align: center; color: #666; font-size: 12px;">
        ⚽ Simulador de Futebol - Versão Completa com Ligas e Hall da Fama | 
        Desenvolvido com Streamlit | 
        Dados carregados dinamicamente
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
