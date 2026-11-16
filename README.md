# Storm Racer G — ROG Ally / Bazzite

Versão 0.1.0. Integração para jogar uma cópia própria de Storm Racer G (2013) no ROG Ally com Bazzite: Proton 11, entrada analógica e atalho Steam.

Este repositório contém somente código próprio e documentação. Traga sua própria cópia do jogo. Nenhuma ROM, DLL, arte, vídeo, captura ou save é distribuído aqui. Projeto independente, sem afiliação aos titulares do jogo.

## Instalação

Requer Python 3 com Pillow, SDL2, Fontconfig, cabextract, xdotool e Proton 11.0 já disponíveis. O instalador não altera pacotes do sistema e instala somente o módulo Wahlap da dependência aberta, além do codec de vídeo necessário, em uma pasta privada.

```bash
python3 tools/instalar.py --game-zip "/caminho/Storm Racer G.zip" --download-dependencies
```

Adicione `~/Games/StormRacerG/jogar.sh` à biblioteca Steam como jogo externo. Deixe a compatibilidade forçada desativada: o script inicia o Proton por conta própria. Inicie pelo Steam no modo jogo.

Para fornecer dependências manualmente, use `--runtime-archive`, `--codec-archive` e `--system-profile`. URLs e SHA-256 estão no instalador e em `source/configure.py`. O instalador recusa sobrescrever uma instalação existente.

## Controles

| Controle | Função |
|---|---|
| Analógico esquerdo | Direção analógica / seleção de carro e pista |
| RT / LT | Acelerador / freio |
| A | Iniciar e confirmar; selecionar a opção no menu de pausa |
| X | Nitro |
| B | Voltar |
| Direcional | Navegação |
| Menu / Start | Abrir o menu de pausa e retomar |
| LB + RB | Menu técnico |

A configuração lê o controle virtual Xbox One Elite 2 do InputPlumber. Não usa o controle físico que já está capturado pelo serviço.

## Funcionamento

- Texto em inglês e unidades métricas já presentes nesta revisão.
- A etapa de tirar foto é pulada: depois de escolher a direção/derrapagem, o jogo segue para a preparação da corrida, com o avatar padrão.
- Renderização configurada em 1920×1080, janela sem bordas na tela do Ally. Os recursos gráficos e a interface mantêm a arte original.
- Jogo local; a lista de servidores de sincronização é esvaziada. Multiplayer em rede e gabinete de movimento não são parte desta integração.
- Interface de controles a 125 Hz, comunicação TCP somente em loopback.
- Avisos da versão de desenvolvimento deixam de restaurar o console sobre a partida.
- Pausa com interface própria em inglês: PAUSED, RESUME e INFINITE BOOST — YES / NO. Use o direcional para escolher e A para confirmar; B ou Menu retoma. O cheat começa em NO a cada abertura do jogo, usa a opção nativa de boost infinito e pode ser alterado durante a corrida. X continua acionando o boost.
- Enquanto o menu está aberto, o processo do jogo fica parado e seus relógios descontam o intervalo da pausa.
- Salvamento e carregamento automáticos: carros e pistas liberados e pontos de desbloqueio continuam disponíveis ao reabrir o jogo. Tempos e estatísticas usam os arquivos nativos, com cópias de segurança automáticas.

## Progresso automático

Não é preciso apertar um botão para salvar ou carregar. O progresso fica na pasta privada `saves/`, com duas cópias verificadas de `progress.json`. As conquistas são observadas a cada 250 ms e gravadas quando mudam; o fim da sessão arcade não zera mais os desbloqueios.

Os recordes nativos ficam em `game/assets/save/` e o histórico em `game/bin/racing.db`. São copiados a cada cinco segundos quando há alterações, usando o backup consistente do SQLite. Na abertura, arquivos nativos ausentes ou danificados são recuperados da cópia de segurança; arquivos válidos mais recentes são preservados. As rotinas locais que descartavam histórico por idade, quantidade ou sincronização foram desativadas. O registro de resultados em sessões sem fichas foi habilitado.

É um perfil local único. A partida começa pelo menu com as conquistas anteriores; não é um save state que retoma o carro no meio da pista. Tempos e resultados dependem de a corrida chegar à etapa em que o próprio jogo os registra. O sistema preserva o progresso existente nos arquivos e na sessão atual; não recupera conquistas que já tinham sido apagadas antes da instalação.

Para copiar o progresso a outro dispositivo, feche o jogo e copie `saves/`, `game/assets/save/` e `game/bin/racing.db`. Nenhum desses dados entra no repositório público.

Veja [validação](docs/VALIDACAO.md) e [dependências](docs/DEPENDENCIAS.md).

## Artes

As artes são privadas. Forneça cinco imagens em `artes/`: `portrait.png` (2:3), `hero.png` (panorâmica, aproximadamente 3:1), `landscape.png` (16:9), `logo.png` (RGBA com fundo transparente) e `icon.png` (quadrado). Capa, banner, imagem horizontal e ícone também aceitam JPG; PNG tem preferência quando os dois existem. Cada peça deve ter sua própria composição, sem esticar a mesma imagem para formatos diferentes.

Use `python3 tools/instalar_artes.py --root ... --app-id ... --account ...`, com o Steam aberto e sua interface de depuração local disponível. O instalador valida as proporções e a transparência, preserva uma cópia das imagens anteriores do Steam e confere cada arquivo instalado por SHA-256. Dimensões e hashes ficam em `logs/artwork-verification.json`. Nenhuma imagem acompanha este projeto.

## Publicação

```bash
python3 tools/publicar_pacote.py --check
python3 tools/publicar_pacote.py
```

Somente os arquivos listados em `PUBLIC_FILES.txt` entram no pacote. Não inicialize Git na pasta privada que contém o jogo.
