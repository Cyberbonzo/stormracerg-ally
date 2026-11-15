# Dependências externas

- [Windows Arcade Loader](https://github.com/aderumier/windowsarcadeloader): módulo Wahlap da release v0.1. Seu código implementa a placa de entradas e as correções de compatibilidade. A integração própria fala o protocolo TCP documentado pelo projeto. O perfil de Storm Racer G é obtido do commit `dd23fdc15e88d8b09a62d712d3d1e5a7d99ae94d`, com SHA-256 verificado. Código e binários desse projeto não estão incluídos neste repositório.
- [Proton](https://github.com/ValveSoftware/Proton): versão 11.0 instalada pelo Steam; prefixo exclusivo em `compatdata/`.
- Microsoft WMV9 VCM: DLL extraída do pacote oficial KB2845142, necessária para vídeos WMV3/AVI do jogo. Download direto da Microsoft e checksum documentados no instalador, conforme a receita do [Winetricks](https://github.com/Winetricks/winetricks). Nenhum instalador é executado e nenhum arquivo Microsoft é redistribuído aqui.
- Python, Pillow, SDL2 e Fontconfig já fornecidos pelo Bazzite usado no teste. Nenhuma dependência adicional foi instalada no sistema.

O hash da revisão de `bin/racing.exe` suportada é `e9370d75a93ab55739a08c2f88297ce80a6185f8f2b82590990999da3a97a5f7`. Outras revisões exigem análise própria; não aplicar offsets às cegas.
