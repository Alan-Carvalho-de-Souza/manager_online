# Arquivo: utils/io.py
import pandas as pd
import os
import datetime
import streamlit as st
import base64
from pathlib import Path

# Caminho para os arquivos de dados
DATA_DIR = "data"
HISTORICO_ARQUIVO = os.path.join(DATA_DIR, "historico_partidas.csv")
CLUBES_ARQUIVO = os.path.join(DATA_DIR, "clubes_utf8.csv")
JOGADORES_ARQUIVO = os.path.join(DATA_DIR, "jogadores_utf8.csv")
LOGOS_DIR = os.path.join("static", "logos")

def carregar_csv_multiplas_codificacoes(caminho_arquivo):
    """
    Tenta carregar um CSV com múltiplas codificações.
    SOLUÇÃO DEFINITIVA para o erro de codificação.
    """
    print(f"🔄 Tentando carregar: {caminho_arquivo}")
    
    # Lista de todas as codificações possíveis
    codificacoes = [
        'cp1252',      # Windows-1252 (mais provável para byte 0xfa)
        'iso-8859-1',  # Latin-1
        'windows-1252', # Explícito
        'utf-8',       # UTF-8 padrão
        'latin1',      # Fallback
        'utf-16',      # Unicode
        'cp850'        # Code page alternativo
    ]
    
    for encoding in codificacoes:
        try:
            print(f"  🧪 Testando {encoding}...")
            df = pd.read_csv(caminho_arquivo, encoding=encoding)
            print(f"  ✅ SUCESSO com {encoding}!")
            return df, encoding
        except (UnicodeDecodeError, UnicodeError):
            print(f"  ❌ Falhou com {encoding}")
            continue
        except Exception as e:
            print(f"  ⚠️ Erro com {encoding}: {e}")
            continue
    
    # Último recurso: ignorar caracteres problemáticos
    try:
        print("  🔧 Último recurso: UTF-8 ignorando erros...")
        df = pd.read_csv(caminho_arquivo, encoding='utf-8', errors='ignore')
        print("  ✅ Carregado ignorando caracteres problemáticos!")
        return df, 'utf-8-ignore'
    except Exception as e:
        print(f"  ❌ FALHA TOTAL: {e}")
        return None, None

def get_logo_base64(time_nome, logo_arquivo):
    """
    Converte a imagem do logo para base64 para exibição no Streamlit.
    Se a imagem não for encontrada, retorna None.
    """
    if not logo_arquivo:
        return None
    
    os.makedirs(LOGOS_DIR, exist_ok=True)
    logo_path = os.path.join(LOGOS_DIR, logo_arquivo)
    
    if not os.path.isfile(logo_path):
        alt_names = [
            f"{time_nome.lower()}.png",
            f"{time_nome.lower()}.jpg",
            f"{time_nome.lower().replace(' ', '')}.png",
            f"{time_nome.lower().replace(' ', '')}.jpg"
        ]
        
        for alt_name in alt_names:
            alt_path = os.path.join(LOGOS_DIR, alt_name)
            if os.path.isfile(alt_path):
                logo_path = alt_path
                break
        else:
            return None
    
    try:
        with open(logo_path, "rb") as img_file:
            return base64.b64encode(img_file.read()).decode()
    except Exception as e:
        st.warning(f"Erro ao carregar logo para {time_nome}: {e}")
        return None

def carregar_clubes(arquivo=None):
    """Carrega os dados dos clubes com tratamento de codificação robusto."""
    if arquivo is None:
        arquivo = CLUBES_ARQUIVO
    
    os.makedirs(DATA_DIR, exist_ok=True)
    os.makedirs(LOGOS_DIR, exist_ok=True)
    
    try:
        print("🏟️ Carregando clubes...")
        df, encoding_used = carregar_csv_multiplas_codificacoes(arquivo)
        
        if df is None:
            st.error(f"Erro: Não foi possível carregar o arquivo de clubes: {arquivo}")
            return {}
        
        st.success(f"✅ Clubes carregados com codificação: {encoding_used}")
        
        clubes = {}
        tem_logos = 'logo_arquivo' in df.columns
        
        for _, linha in df.iterrows():
            logo_arquivo = linha['logo_arquivo'] if tem_logos else None
            logo_base64 = get_logo_base64(linha['nome'], logo_arquivo)
            
            clubes[linha['id']] = {
                'nome': linha['nome'],
                'forca_geral': linha['forca_geral'],
                'jogadores': [],
                'logo_base64': logo_base64
            }
        
        print(f"✅ {len(clubes)} clubes carregados com sucesso!")
        return clubes
        
    except Exception as e:
        st.error(f"Erro ao carregar clubes: {e}")
        return {}

def carregar_jogadores(arquivo=None, clubes=None):
    """
    VERSÃO CORRIGIDA - Carrega jogadores com tratamento robusto de codificação.
    Esta versão resolve o erro: 'utf-8' codec can't decode byte 0xfa
    """
    if arquivo is None:
        arquivo = JOGADORES_ARQUIVO
    
    if not clubes:
        st.warning("Nenhum clube fornecido para associar os jogadores.")
        return
    
    try:
        print("👥 Carregando jogadores...")
        
        # SOLUÇÃO: Usar função de múltiplas codificações
        df, encoding_used = carregar_csv_multiplas_codificacoes(arquivo)
        
        if df is None:
            st.error(f"❌ ERRO: Não foi possível carregar o arquivo de jogadores: {arquivo}")
            st.error("Verifique se o arquivo existe e não está corrompido.")
            return
        
        # Sucesso no carregamento!
        st.success(f"✅ Jogadores carregados com codificação: {encoding_used}")
        print(f"📊 {len(df)} linhas carregadas do arquivo de jogadores")
        
        # Verificar colunas necessárias
        colunas_necessarias = ['nome', 'posicao', 'habilidade', 'clube_id']
        if not all(col in df.columns for col in colunas_necessarias):
            st.error(f"Erro: Colunas necessárias não encontradas: {colunas_necessarias}")
            st.write(f"Colunas disponíveis: {list(df.columns)}")
            return
        
        # Processar jogadores
        jogadores_carregados = 0
        jogadores_erro = 0
        
        for index, linha in df.iterrows():
            try:
                jogador = {
                    'nome': str(linha['nome']).strip(),
                    'posicao': str(linha['posicao']).strip(),
                    'habilidade': float(linha['habilidade'])
                }
                clube_id = linha['clube_id']
                
                if clube_id in clubes:
                    clubes[clube_id]['jogadores'].append(jogador)
                    jogadores_carregados += 1
                else:
                    print(f"⚠️ Clube ID {clube_id} não encontrado para {jogador['nome']}")
                    jogadores_erro += 1
                    
            except Exception as e:
                print(f"❌ Erro linha {index}: {e}")
                jogadores_erro += 1
                continue
        
        # Relatório final
        st.success(f"🎉 {jogadores_carregados} jogadores carregados com sucesso!")
        
        if jogadores_erro > 0:
            st.warning(f"⚠️ {jogadores_erro} jogadores tiveram problemas no carregamento.")
        
        # Mostrar distribuição por clube
        with st.expander("📊 Distribuição de jogadores por clube"):
            for clube_id, clube in clubes.items():
                num_jogadores = len(clube['jogadores'])
                if num_jogadores > 0:
                    st.write(f"🏟️ **{clube['nome']}**: {num_jogadores} jogadores")
        
        print("✅ Carregamento de jogadores finalizado com sucesso!")
        
    except Exception as e:
        st.error(f"❌ ERRO CRÍTICO ao carregar jogadores: {e}")
        print(f"❌ ERRO CRÍTICO: {e}")
        
        # Dicas para o usuário
        st.info("💡 **Dicas para resolver:**")
        st.write("1. Verifique se o arquivo existe em:", arquivo)
        st.write("2. Abra o arquivo no Excel e salve como 'CSV (UTF-8)'")
        st.write("3. Verifique se o arquivo não está sendo usado por outro programa")

def salvar_resultado(clube1, clube2, gols1, gols2, marcadores_gols):
    """Salva o resultado da partida em um arquivo CSV."""
    os.makedirs(DATA_DIR, exist_ok=True)
    data_atual = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    marcadores_str = ';'.join([f"{jogador}:{minuto}:{time}" for jogador, minuto, time in marcadores_gols])
    
    resultado = pd.DataFrame({
        'data': [data_atual],
        'time_casa': [clube1['nome']],
        'time_visitante': [clube2['nome']],
        'gols_casa': [gols1],
        'gols_visitante': [gols2],
        'vencedor': [clube1['nome'] if gols1 > gols2 else (clube2['nome'] if gols2 > gols1 else 'Empate')],
        'marcadores_gols': [marcadores_str]
    })
    
    try:
        arquivo_existe = os.path.isfile(HISTORICO_ARQUIVO)
        
        if arquivo_existe:
            resultado.to_csv(HISTORICO_ARQUIVO, mode='a', header=False, index=False, encoding='utf-8')
        else:
            resultado.to_csv(HISTORICO_ARQUIVO, index=False, encoding='utf-8')
        
        return True
    except Exception as e:
        st.error(f"Erro ao salvar resultado: {e}")
        return False

def carregar_historico():
    """Carrega o histórico de partidas com tratamento de codificação."""
    if not os.path.isfile(HISTORICO_ARQUIVO):
        return None
    
    try:
        df, encoding_used = carregar_csv_multiplas_codificacoes(HISTORICO_ARQUIVO)
        if df is not None and encoding_used:
            print(f"📊 Histórico carregado com codificação: {encoding_used}")
        return df
    except Exception as e:
        try:
            backup_file = HISTORICO_ARQUIVO + '.bak'
            os.rename(HISTORICO_ARQUIVO, backup_file)
            st.warning(f"Arquivo de histórico problemático. Backup criado: {backup_file}")
            st.warning("Um novo arquivo de histórico será criado.")
        except:
            st.error("Não foi possível criar backup do arquivo problemático.")
        return None

def filtrar_historico_por_time(historico, time_nome):
    """Filtra o histórico de partidas por um time específico."""
    if historico is None:
        return None
    
    filtro = (historico['time_casa'] == time_nome) | (historico['time_visitante'] == time_nome)
    return historico[filtro]

def teste_rapido_codificacao():
    """Função para testar rapidamente se o problema foi resolvido."""
    st.subheader("🧪 Teste Rápido de Codificação")
    
    if st.button("🔍 Testar Carregamento de Jogadores"):
        arquivo = JOGADORES_ARQUIVO
        
        if os.path.exists(arquivo):
            st.info(f"Testando arquivo: {arquivo}")
            
            df, encoding = carregar_csv_multiplas_codificacoes(arquivo)
            
            if df is not None:
                st.success(f"✅ SUCESSO! Arquivo carregado com: {encoding}")
                st.write(f"📊 Linhas: {len(df)}")
                st.write(f"📋 Colunas: {list(df.columns)}")
                
                # Mostrar preview
                st.write("**Preview dos primeiros 5 jogadores:**")
                st.dataframe(df.head())
                
            else:
                st.error("❌ FALHA: Não foi possível carregar o arquivo")
        else:
            st.error(f"❌ Arquivo não encontrado: {arquivo}")

# Instruções de uso no final do arquivo como comentário
"""
🚀 COMO USAR ESTA VERSÃO CORRIGIDA:

1. Substitua completamente seu arquivo utils/io.py por este código

2. No seu arquivo principal, para testar se funcionou, adicione:

```python
from utils.io import teste_rapido_codificacao

# Em algum lugar do seu app
if st.checkbox("🧪 Testar Codificação"):
    teste_rapido_codificacao()
```

3. Execute seu app normalmente - o erro deve desaparecer!

O problema do byte 0xfa será resolvido automaticamente usando CP1252 ou ISO-8859-1.
"""