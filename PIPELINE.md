# Cómo se produce y publica cada Short de LogiDatos

Canal: **LogiDatos** (YouTube Shorts de curiosidades generales, en español latino).
Objetivo: 2 videos por día, temas que nunca se repiten (ver `topics.md`), aptos para monetizar.

## 1. Tema y guion
- Lee `topics.md`. Elige una curiosidad NUEVA, sorprendente y visual (animales, cuerpo humano, espacio, historia, física, comida, tecnología…). Varía las categorías.
- Verifica cada dato con búsqueda web en fuentes confiables (Smithsonian, Live Science, National Geographic, NASA, universidades). Si un dato es dudoso, no lo uses.
- Guion de 30–45 s (≈90–110 palabras), español latino neutro:
  - Gancho en la primera frase (pregunta o dato impactante, sin decir el nombre al inicio si genera intriga).
  - 2–3 datos explicados simple.
  - Cierre: resumen corto + "¿Qué otro … quieres que expliquemos? Síguenos en LogiDatos."

## 2. Voz (ElevenLabs, conector)
- `creative_create_flow` (nombre "LogiDatos #N – tema").
- `creative_generate_speech`: `voice_id = dlGxemPxFMTY7iXagmOj` (Fernando Martínez), `model_id = eleven_v4`, `generations_count = 1`, `flow_id` del paso anterior.
- Espera con `creative_get_flow_run_status` y toma el `content_url` del mp3.
- Fija la toma con `creative_add_flow_asset_node` (modality audio, generation_id) y transcribe con `creative_transcribe_audio` (`model_id eleven_scribe_v1`, `connect_from` = ese nodo). Es gratis y da tiempos por palabra.
- Descarga con `curl` el mp3 y el `words_download_url` (el dominio elevenlabsusercontent.com está permitido).
- NO generar video ni imágenes con IA en ElevenLabs (caro). El video se dibuja en código.

## 3. Video (dibujado en código)
- `pip install --break-system-packages pycairo` si falta. Usa `pipeline/ejemplo_01_pulpo.py` como plantilla: fondo, subtítulos palabra por palabra (amarillo #FFD23F en la palabra activa), etiqueta LogiDatos arriba, tarjeta final con logo + "SÍGUENOS".
- Dibuja animaciones nuevas y propias para el tema (íconos, diagramas, personajes simples, comparaciones, contadores). Una escena por idea del guion, sincronizadas con los tiempos de las palabras.
- 1080×1920, 30 fps, H.264 CRF 18 preset veryfast, audio AAC 192k.
- **Música de fondo (obligatoria desde el #3):** solo música ORIGINAL generada con `pipeline/musica.py` (sintetizada en código, sin samples ni pistas de terceros → sin copyright). Nunca descargues música de internet ni la generes con IA.
  - Elige el preset según el tema: `espacio` (espacio, planetas, océano profundo), `curioso` (animales, cuerpo humano, comida), `misterio` (historia, misterios, récords), `energia` (tecnología, física, inventos, deportes). Usa como `--seed` el número del video para que cada uno suene distinto.
  - `python3 pipeline/musica.py gen --dur <TOTAL> --preset <preset> --seed <N> --out build/musica.wav`
  - En el render, en lugar de unir solo la voz al video mudo, mezcla: `python3 pipeline/musica.py mix build/silent.mp4 dl/voz.mp3 build/musica.wav <FINAL>.mp4 --total <TOTAL>` (la música queda ~15 dB bajo la voz y se reduce sola cuando habla el narrador).
  - Verifica con `ffmpeg -af volumedetect` que el volumen medio final quede entre -18 y -14 dB y el máximo por debajo de -1 dB.
- Antes de renderizar completo, revisa 6–8 cuadros de vista previa y corrige solapamientos.
- Nombre: `LogiDatos_NN_tema_corto.mp4`.

## 4. Publicación
- Repo `Oscar-Perez2/logidatos-videos`, rama `videos`: copia el mp4 a `videos/`, agrega la línea en `topics.md`, commit y push.
- Enlace público: `https://raw.githubusercontent.com/Oscar-Perez2/logidatos-videos/videos/videos/<archivo>.mp4`
- Metricool `createScheduledPost`: `blogId 8288543`, `autoPublish true`, `media` = enlace anterior, zona horaria America/Santo_Domingo. Se publica en las CUATRO redes: `providers` = youtube, facebook, instagram, tiktok.
  - `youtubeData` = {title (≤70 caracteres, con gancho y "#shorts"), type "short", privacy "public", tags, category "EDUCATION", madeForKids false, isAiGeneratedContent false}
  - `facebookData` = {type "REEL", title = el mismo título sin "#shorts"}
  - `instagramData` = {type "REEL", showReelOnFeed true, isAiGenerated false}
  - `tiktokData` = {privacyOption "PUBLIC_TO_EVERYONE", title = el mismo título sin "#shorts"}
  - `text` = descripción con 2–3 frases + "🔔 Sigue a LogiDatos para más curiosidades en menos de un minuto." + 5 hashtags.
- Horarios: corrida de la mañana → publicar a las 10:00; corrida de la tarde → publicar a las 18:00 (si ya hay algo a esa hora, la siguiente hora libre).
