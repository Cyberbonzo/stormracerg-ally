# Validação 0.1.0

Hardware: ROG Ally X com Bazzite, Proton 11.0 e InputPlumber.

- Inicialização pelo Steam, tela inteira e menus em inglês observados por captura.
- Usuário confirmou analógico, acelerador, freio e confirmação no controle do Ally.
- Corrida e transição para desbloqueio de carro observadas.
- Partida iniciada com zero créditos; nesta revisão não foi necessário inserir fichas.
- Pausa pelo Menu testada em corrida: duas capturas idênticas durante a parada; ao retomar, o cronômetro descontou apenas o tempo jogado. Os relógios QPC e GetTickCount do executável compartilham o desconto da pausa.
- Instalador completo executado em diretório temporário no Ally a partir do ZIP particular e dos arquivos de dependências verificados.
- Menu em inglês inspecionado em capturas reais do Ally: NO e YES. O toggle foi conferido na opção nativa Infinite Boost do jogo; B retornou à partida.
- Usuário confirmou o funcionamento do X no controle físico após a correção.
- Boost no X usando o bit 0x04 da entrada de corrida; alinhamento dos dois campos de botões do módulo de I/O. Acionamento no X validado após reiniciar, com efeito no escapamento e consumo da barra em NO; com YES, nitro ativo mantendo carga cheia.
- Renderização 1920×1080 confirmada no dispositivo Direct3D. Amostra de 12 segundos ativos: 59,90–60,98 FPS (média 60,10); não garante desempenho em todas as pistas.
- Velocidade e distância em unidades métricas observadas na corrida.
- Console de diagnóstico: identificado o roubo de foco após aviso de áudio ausente. A correção retorna a opção de continuar sem restaurar a janela do console; o jogo foi reiniciado e testado novamente.
- Artes privadas renovadas com cinco composições distintas: capa 1024×1536, banner 2172×724, horizontal 1672×941, logo RGBA 2172×724 e ícone 1254×1254. Proporções e transparência validadas; os cinco arquivos instalados no Steam conferidos por SHA-256. Banner e logo inspecionados juntos em captura real do modo jogo do Ally. Imagens permanecem fora do pacote público.
- Autosave: sete carros extras existentes foram capturados e recuperados automaticamente após encerrar e reabrir o processo.
- Banco nativo: resultado novo de 119,518661 segundos registrado e conferido novamente após reiniciar. Gravação de sessões sem fichas habilitada na inicialização do gerenciador de recordes.
- Recuperação automatizada testada com dados sintéticos: perfil truncado, save nativo danificado e banco corrompido. Os backups recuperaram os dados; um banco válido com resultado mais recente foi preservado.
- Configuração aplicada duas vezes com os mesmos hashes finais, sem duplicação de opções.
- Etapa da foto: sequência observada após reiniciar `TITLE → FIND_SERVER → LEVEL_SELECT → CAR_SELECT → DRIFT_SELECT → WAITING_SCREEN → START_RACE → LOADING_SCREEN → ROLLING_START → RACE_RUNNING`. O estado `PHOTO_TAKING` não foi executado. A preparação interna da tela de espera foi mantida.
- Pausa testada com a alteração da foto instalada: duas capturas idênticas durante a pausa e imagem diferente ao retomar.

Limitações: o conteúdo fornecido é uma versão de desenvolvimento com alguns recursos ausentes, incluindo avisos de áudio e objetos visuais de checkpoints. As correções upstream contornam os acessos inválidos; não recriam os recursos. Todas as pistas e situações de corrida ainda não foram verificadas. Não há promessa de compatibilidade com outras revisões.
