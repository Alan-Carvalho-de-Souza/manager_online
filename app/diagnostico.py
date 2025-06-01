# Arquivo: diagnostico.py - Execute este arquivo para diagnosticar o problema
import os
import sys

print("🔍 DIAGNÓSTICO DO PROBLEMA DE IMPORTAÇÃO")
print("=" * 50)

# 1. Verificar diretório atual
print(f"📁 Diretório atual: {os.getcwd()}")

# 2. Verificar se a pasta app existe
if os.path.exists("app"):
    print("✅ Pasta 'app' encontrada")
    
    # Listar arquivos na pasta app
    arquivos_app = os.listdir("app")
    print(f"📄 Arquivos na pasta app: {arquivos_app}")
    
    # Verificar arquivos específicos
    if "ligas.py" in arquivos_app:
        print("✅ Arquivo 'ligas.py' encontrado")
        
        # Verificar conteúdo do arquivo
        try:
            with open("app/ligas.py", "r", encoding="utf-8") as f:
                conteudo = f.read()
            print(f"📝 Tamanho do arquivo ligas.py: {len(conteudo)} caracteres")
            
            if len(conteudo) == 0:
                print("❌ PROBLEMA: O arquivo ligas.py está vazio!")
            else:
                print("✅ O arquivo ligas.py tem conteúdo")
                
        except Exception as e:
            print(f"❌ Erro ao ler ligas.py: {e}")
    else:
        print("❌ Arquivo 'ligas.py' NÃO encontrado")
    
    if "simulacao_automatica.py" in arquivos_app:
        print("✅ Arquivo 'simulacao_automatica.py' encontrado")
    else:
        print("❌ Arquivo 'simulacao_automatica.py' NÃO encontrado")
        
else:
    print("❌ Pasta 'app' NÃO encontrada")

# 3. Verificar sys.path
print(f"\n🛤️ Python path atual:")
for i, path in enumerate(sys.path):
    print(f"  {i}: {path}")

# 4. Tentar importar manualmente
print(f"\n🧪 TESTE DE IMPORTAÇÃO:")
try:
    # Adicionar diretório atual ao path se necessário
    if os.getcwd() not in sys.path:
        sys.path.insert(0, os.getcwd())
        print("📌 Adicionado diretório atual ao Python path")
    
    # Tentar importar
    from app.ligas import pagina_ligas
    print("✅ SUCESSO: Importação de app.ligas funcionou!")
    
except ImportError as e:
    print(f"❌ ERRO de importação: {e}")
    
except Exception as e:
    print(f"❌ ERRO geral: {e}")

# 5. Verificar versão do Python
print(f"\n🐍 Versão do Python: {sys.version}")

print("\n" + "=" * 50)
print("🔧 INSTRUÇÕES BASEADAS NO DIAGNÓSTICO:")

if not os.path.exists("app"):
    print("1. ❌ Crie a pasta 'app' no diretório atual")
elif "ligas.py" not in os.listdir("app"):
    print("2. ❌ Crie o arquivo 'app/ligas.py'")
else:
    print("3. ✅ Estrutura de arquivos parece correta")
    print("   Verifique se há erros de sintaxe no arquivo ligas.py")

print("\n💡 Execute este script no mesmo diretório onde você roda 'streamlit run app/main.py'")
