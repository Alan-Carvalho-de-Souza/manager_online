# Arquivo: app/classificacao.py
import pandas as pd
import streamlit as st
import base64
import os

def gerar_tabela_classificacao(historico):
    """
    Gera a tabela de classificação com base no histórico de partidas.
    3 pontos por vitória, 1 ponto por empate.
    
    Args:
        historico (DataFrame): DataFrame com o histórico de partidas.
        
    Returns:
        DataFrame or None: DataFrame com a tabela de classificação ou None se o histórico for None.
    """
    if historico is None or historico.empty:
        return None
    
    # Inicializa um dicionário para armazenar as estatísticas dos times
    tabela = {}
    
    # Processa cada partida do histórico
    for _, partida in historico.iterrows():
        time_casa = partida['time_casa']
        time_visitante = partida['time_visitante']
        gols_casa = partida['gols_casa']
        gols_visitante = partida['gols_visitante']
        vencedor = partida['vencedor']
        
        # Inicializa estatísticas para os times se ainda não existirem
        for time in [time_casa, time_visitante]:
            if time not in tabela:
                tabela[time] = {
                    'time': time,
                    'jogos': 0,
                    'vitorias': 0,
                    'empates': 0,
                    'derrotas': 0,
                    'gols_pro': 0,
                    'gols_contra': 0,
                    'saldo_gols': 0,
                    'pontos': 0
                }
        
        # Atualiza estatísticas para o time da casa
        tabela[time_casa]['jogos'] += 1
        tabela[time_casa]['gols_pro'] += gols_casa
        tabela[time_casa]['gols_contra'] += gols_visitante
        
        # Atualiza estatísticas para o time visitante
        tabela[time_visitante]['jogos'] += 1
        tabela[time_visitante]['gols_pro'] += gols_visitante
        tabela[time_visitante]['gols_contra'] += gols_casa
        
        # Atualiza vitórias, empates, derrotas e pontos
        if vencedor == 'Empate':
            # Empate
            tabela[time_casa]['empates'] += 1
            tabela[time_visitante]['empates'] += 1
            tabela[time_casa]['pontos'] += 1
            tabela[time_visitante]['pontos'] += 1
        elif vencedor == time_casa:
            # Time da casa venceu
            tabela[time_casa]['vitorias'] += 1
            tabela[time_visitante]['derrotas'] += 1
            tabela[time_casa]['pontos'] += 3
        else:
            # Time visitante venceu
            tabela[time_visitante]['vitorias'] += 1
            tabela[time_casa]['derrotas'] += 1
            tabela[time_visitante]['pontos'] += 3
    
    # Calcula o saldo de gols
    for time_stats in tabela.values():
        time_stats['saldo_gols'] = time_stats['gols_pro'] - time_stats['gols_contra']
    
    # Converte o dicionário para DataFrame
    df_tabela = pd.DataFrame(list(tabela.values()))
    
    # Ordena a tabela por pontos (decrescente), depois saldo de gols, depois gols marcados
    df_tabela = df_tabela.sort_values(
        by=['pontos', 'saldo_gols', 'gols_pro', 'vitorias'], 
        ascending=[False, False, False, False]
    )
    
    # Adiciona a posição na tabela como um novo índice
    df_tabela = df_tabela.reset_index(drop=True)
    df_tabela.index = df_tabela.index + 1  # Começa do 1 em vez de 0
    
    # Renomeia o índice para "Posição"
    df_tabela.index.name = "Pos"
    
    return df_tabela

def gerar_tabela_artilharia(historico):
    """
    Gera a tabela de artilharia do campeonato.
    
    Args:
        historico (DataFrame): DataFrame com o histórico de partidas.
        
    Returns:
        DataFrame or None: DataFrame com a tabela de artilharia ou None se não houver dados.
    """
    if historico is None or historico.empty or 'marcadores_gols' not in historico.columns:
        return None
    
    try:
        # Extrair todos os marcadores de gols
        artilheiros_campeonato = {}
        
        for _, partida in historico.iterrows():
            if isinstance(partida['marcadores_gols'], str) and partida['marcadores_gols']:
                marcadores_lista = partida['marcadores_gols'].split(';')
                for marcador_info in marcadores_lista:
                    if marcador_info:
                        partes = marcador_info.split(':')
                        if len(partes) >= 3:
                            jogador, _, time = partes
                            chave_jogador = f"{jogador} ({time})"
                            if chave_jogador in artilheiros_campeonato:
                                artilheiros_campeonato[chave_jogador] += 1
                            else:
                                artilheiros_campeonato[chave_jogador] = 1
        
        if not artilheiros_campeonato:
            return None
            
        # Ordenar artilheiros por número de gols (decrescente)
        artilheiros_ordenados = sorted(artilheiros_campeonato.items(), key=lambda x: x[1], reverse=True)
        
        # Criar DataFrame para mostrar os artilheiros
        artilheiros_df = pd.DataFrame(artilheiros_ordenados, columns=['Jogador', 'Gols'])
        
        # Adicionar ranking
        artilheiros_df.index = artilheiros_df.index + 1
        artilheiros_df.index.name = "Pos"
        
        return artilheiros_df
    except Exception as e:
        st.warning(f"Erro ao gerar tabela de artilharia: {e}")
        return None

def exibir_time_com_logo(time_nome, clubes):
    """
    Retorna HTML para exibir o nome do time com seu logo.
    
    Args:
        time_nome (str): Nome do time
        clubes (dict): Dicionário com dados dos clubes
    
    Returns:
        str: HTML formatado com logo e nome do time
    """
    # Encontrar o clube pelo nome
    clube_id = None
    for cid, clube in clubes.items():
        if clube['nome'] == time_nome:
            clube_id = cid
            break
    
    if clube_id is None or 'logo_base64' not in clubes[clube_id] or not clubes[clube_id]['logo_base64']:
        return time_nome
    
    # Retornar HTML com logo
    return f"""
    <div style="display: flex; align-items: center;">
        <img src="data:image/png;base64,{clubes[clube_id]['logo_base64']}" 
             style="max-width: 25px; max-height: 25px; margin-right: 6px;" alt="{time_nome}">
        <span>{time_nome}</span>
    </div>
    """

def exibir_classificacao_com_logos(tabela, clubes):
    """
    Exibe a tabela de classificação com logos dos times.
    Combinando o uso de dataframe do Streamlit e uma versão alternativa com colunas.
    
    Args:
        tabela (DataFrame): Tabela de classificação
        clubes (dict): Dicionário com dados dos clubes
    """
    if tabela is None:
        st.info("Não há partidas suficientes para gerar a classificação.")
        return
    
    # Criar uma tabela com uma coluna adicional para os times com logos
    # Esta é a abordagem para mostrar logos diretamente na tabela
    tabela_display = tabela.copy()
    
    # Opção de exibição: Tabela do Streamlit com coluna personalizada
    st.subheader("Tabela de Classificação")
    
   # Colunas regulares - VERSÃO REORDENADA
    colunas = {
    "time": "Time",
    "jogos": "J",
    "pontos": st.column_config.NumberColumn(
        "PTS",
        help="Pontos (3 por vitória, 1 por empate)",
        format="%d",
    ),
    "vitorias": "V",
    "empates": "E",
    "derrotas": "D",
    "gols_pro": "GP",
    "gols_contra": "GC",
    "saldo_gols": "SG",
}
    
    # Exibir a tabela usando o dataframe do Streamlit
    st.dataframe(
        tabela_display,
        column_config=colunas,
        hide_index=False
    )
    
    # Versão alternativa usando colunas do Streamlit
    with st.expander("Ver tabela com logos"):
        st.markdown("### Tabela de Classificação com Logos")
        
        # Cabeçalho
        col_rank, col_time, col_pts, col_stats = st.columns([1, 3, 1, 4])
        with col_rank:
            st.markdown("**Pos**")
        with col_time:
            st.markdown("**Time**")
        with col_pts:
            st.markdown("**PTS**")
        with col_stats:
            st.markdown("**J · V · E · D · GP · GC · SG**")
        
        # Dividir em pequenos grupos para melhor desempenho
        # Mostrar apenas os primeiros 20 times (ou menos se houver menos)
        num_times = min(20, len(tabela))
        
        # Usar um separador horizontal
        st.markdown("<hr style='margin: 5px 0; background-color: #ddd;'>", unsafe_allow_html=True)
        
        # Dados da tabela
        for idx, row in tabela.iloc[:num_times].iterrows():
            time_nome = row['time']
            col_rank, col_time, col_pts, col_stats = st.columns([1, 3, 1, 4])
            
            with col_rank:
                st.write(f"{idx}")
            
            with col_time:
                # Encontrar o logo
                logo_found = False
                for cid, clube in clubes.items():
                    if clube['nome'] == time_nome and clube.get('logo_base64'):
                        st.markdown(
                            f"""<div style="display: flex; align-items: center;">
                               <img src="data:image/png;base64,{clube['logo_base64']}" 
                                    style="width: 24px; height: 24px; margin-right: 8px;">
                               <span>{time_nome}</span>
                            </div>""",
                            unsafe_allow_html=True
                        )
                        logo_found = True
                        break
                
                if not logo_found:
                    st.write(time_nome)
            
            with col_pts:
                st.markdown(f"**{row['pontos']}**")
            
            with col_stats:
                stats = f"{row['jogos']} · {row['vitorias']} · {row['empates']} · {row['derrotas']} · {row['gols_pro']} · {row['gols_contra']} · {row['saldo_gols']}"
                st.write(stats)
            
            # Opcional: Adicionar divisor entre linhas
            if idx < num_times:
                st.markdown("<hr style='margin: 2px 0; background-color: #f0f0f0;'>", unsafe_allow_html=True)
        
        # Se houver mais times, indicar isso
        if len(tabela) > num_times:
            st.info(f"Exibindo os primeiros {num_times} de {len(tabela)} times")