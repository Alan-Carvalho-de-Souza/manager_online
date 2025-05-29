# Arquivo: app/main.py
import streamlit as st
import pandas as pd
import re

# Adiciona o diretório raiz ao sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Importar os módulos da aplicação
import sys
import os
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

# Tentar importar com tratamento de erro
try:
    from utils.io import carregar_clubes, carregar_jogadores, carregar_historico, filtrar_historico_por_time
except ModuleNotFoundError as e:
    st.error(f"Erro ao importar módulo utils: {e}")
    st.error(f"Diretório atual: {os.getcwd()}")
    st.error(f"Arquivos disponíveis: {os.listdir('.')}")
    if os.path.exists('utils'):
        st.error(f"Arquivos em utils: {os.listdir('utils')}")
    else:
        st.error("Pasta utils não encontrada!")
    st.stop()
from app.simulacao import simular_partida
from app.estatisticas import exibir_estatisticas_time
from app.classificacao import gerar_tabela_classificacao, gerar_tabela_artilharia, exibir_classificacao_com_logos

# NOVA IMPORTAÇÃO PARA TORNEIOS
try:
    from app.torneios import pagina_torneios, exibir_classificacao_geral_torneios
    TORNEIOS_DISPONIVEL = True
except ImportError:
    TORNEIOS_DISPONIVEL = False
    st.sidebar.warning("⚠️ Módulo de torneios não encontrado. Crie o arquivo app/torneios.py")

def main():
    """
    Função principal que inicia a aplicação Streamlit.
    """
    # Configurações da página
    st.set_page_config(
        page_title="⚽ Simulador de Futebol Completo",
        page_icon="⚽",
        layout="wide",
        initial_sidebar_state="expanded",
    )
    
    st.title("⚽ Simulador de Partidas de Futebol")
    
    # Carregar dados dos clubes e jogadores
    with st.spinner("🔄 Carregando dados..."):
        clubes = carregar_clubes()
        carregar_jogadores(clubes=clubes)
    
    # Exibir informações na sidebar
    st.sidebar.title("📊 Informações Gerais")
    
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
    
    # CRIAR ABAS - AGORA COM CLASSIFICAÇÃO DE TORNEIOS
    if TORNEIOS_DISPONIVEL:
        tab1, tab2, tab3, tab4, tab5 = st.tabs([
            "⚽ Simulador", 
            "📊 Histórico", 
            "🏆 Classificação", 
            "🏟️ Torneios",
            "👑 Hall da Fama"  # NOVA ABA
        ])
    else:
        tab1, tab2, tab3 = st.tabs([
            "⚽ Simulador", 
            "📊 Histórico", 
            "🏆 Classificação"
        ])
        tab4 = tab5 = None
    
    # ABA 1: SIMULADOR
    with tab1:
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
    
    # ABA 2: HISTÓRICO
    with tab2:
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
                # Ordenar por data (mais recente primeiro)
                historico_completo = historico.sort_values('data', ascending=False)
                
                # Limitar a exibição para melhor performance
                limite = st.slider("Número de partidas a exibir:", 5, len(historico), min(50, len(historico)))
                
                st.dataframe(
                    historico_completo.head(limite),
                    hide_index=True,
                    use_container_width=True
                )
                
                if limite < len(historico):
                    st.info(f"Exibindo {limite} de {len(historico)} partidas. Ajuste o slider para ver mais.")
    
    # ABA 3: CLASSIFICAÇÃO
    with tab3:
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
                artilheiros_df = gerar_tabela_artilharia(historico)
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
    
    # ABA 4: TORNEIOS
    if TORNEIOS_DISPONIVEL and tab4 is not None:
        with tab4:
            try:
                pagina_torneios(clubes)
            except Exception as e:
                st.error(f"❌ Erro ao carregar módulo de torneios: {e}")
                st.info("📝 Verifique se o arquivo app/torneios.py existe e está correto.")
    
    # ABA 5: HALL DA FAMA DOS TORNEIOS (NOVA!)
    if TORNEIOS_DISPONIVEL and tab5 is not None:
        with tab5:
            try:
                exibir_classificacao_geral_torneios(clubes)
            except Exception as e:
                st.error(f"❌ Erro ao carregar classificação de torneios: {e}")
                st.info("📝 Verifique se existem torneios realizados.")
    
    # Rodapé com informações
    st.markdown("---")
    st.markdown("""
    <div style="text-align: center; color: #666; font-size: 12px;">
        ⚽ Simulador de Futebol - Versão Completa com Hall da Fama | 
        Desenvolvido com Streamlit | 
        Dados carregados dinamicamente
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
