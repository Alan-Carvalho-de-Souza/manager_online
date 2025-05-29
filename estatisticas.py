# Arquivo: app/estatisticas.py
import streamlit as st
import pandas as pd

def exibir_estatisticas_time(historico, time_nome):
    """
    Exibe estatísticas detalhadas de um time com base no histórico.
    
    Args:
        historico (DataFrame): DataFrame com o histórico de partidas.
        time_nome (str): Nome do time para exibir estatísticas.
    """
    if historico is None or historico.empty:
        st.info(f"Não há partidas registradas para {time_nome}")
        return
    
    # Contador de vitórias, derrotas e empates
    vitorias = len(historico[historico['vencedor'] == time_nome])
    empates = len(historico[historico['vencedor'] == 'Empate'])
    derrotas = len(historico) - vitorias - empates
    
    # Gols marcados e sofridos
    gols_marcados = 0
    gols_sofridos = 0
    
    for _, partida in historico.iterrows():
        if partida['time_casa'] == time_nome:
            gols_marcados += partida['gols_casa']
            gols_sofridos += partida['gols_visitante']
        else:
            gols_marcados += partida['gols_visitante']
            gols_sofridos += partida['gols_casa']
    
    # Exibir estatísticas
    col1, col2, col3 = st.columns(3)
    col1.metric("Vitórias", vitorias)
    col2.metric("Empates", empates)
    col3.metric("Derrotas", derrotas)
    
    col1, col2, col3 = st.columns(3)
    col1.metric("Jogos", len(historico))
    col2.metric("Gols marcados", gols_marcados)
    col3.metric("Gols sofridos", gols_sofridos)
    
    # Histórico de partidas
    st.subheader("Histórico de partidas")
    
    # Formatar o histórico para exibição
    historico_exibicao = historico.copy()
    historico_exibicao['Placar'] = historico_exibicao.apply(
        lambda x: f"{x['time_casa']} {x['gols_casa']} x {x['gols_visitante']} {x['time_visitante']}", 
        axis=1
    )
    
    # Ordenar por data (mais recente primeiro)
    historico_exibicao = historico_exibicao.sort_values('data', ascending=False)
    
    # Exibir a tabela
    st.dataframe(
        historico_exibicao[['data', 'Placar', 'vencedor']],
        column_config={
            "data": "Data",
            "Placar": "Placar",
            "vencedor": "Vencedor"
        },
        hide_index=True
    )
    
    # Se houver informações sobre os marcadores de gols, exibir os artilheiros do time
    if 'marcadores_gols' in historico.columns:
        try:
            # Extrair todos os marcadores de gols do time
            artilheiros = {}
            
            for _, partida in historico.iterrows():
                if isinstance(partida['marcadores_gols'], str) and partida['marcadores_gols']:
                    marcadores_lista = partida['marcadores_gols'].split(';')
                    for marcador_info in marcadores_lista:
                        if marcador_info:
                            partes = marcador_info.split(':')
                            if len(partes) >= 3:
                                jogador, _, time_marcador = partes
                                if time_marcador == time_nome:
                                    if jogador in artilheiros:
                                        artilheiros[jogador] += 1
                                    else:
                                        artilheiros[jogador] = 1
            
            if artilheiros:
                st.subheader("Artilheiros")
                # Ordenar artilheiros por número de gols (decrescente)
                artilheiros_ordenados = sorted(artilheiros.items(), key=lambda x: x[1], reverse=True)
                
                # Criar DataFrame para mostrar os artilheiros
                artilheiros_df = pd.DataFrame(artilheiros_ordenados, columns=['Jogador', 'Gols'])
                
                # Mostrar tabela de artilheiros
                st.dataframe(artilheiros_df, hide_index=True)
        except Exception as e:
            st.warning(f"Não foi possível carregar os artilheiros: {e}")