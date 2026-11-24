# Cómo se produce y publica cada Short de LogiDatos

Canal: **LogiDatos**, curiosidades de TODO tipo en español latino neutro.
Es la ÚNICA marca: YouTube, Facebook, Instagram y TikTok son todas cuentas de LogiDatos.
MedLogicos se cerró el 23-nov-2026: nunca uses ese nombre, su estilo "Neón" ni su carpeta de Drive.
Todo vive en este repositorio (rama `videos`). Nada se sube a Google Drive.

Objetivo: 1 video por día (hasta el 30-nov-2026), temas que nunca se repiten (ver `topics.md`), aptos para monetizar y pensados para que el algoritmo los empuje.

## 0. Qué premia el algoritmo (aplica en cada paso)
- Cada Short se prueba primero con un grupo pequeño de desconocidos. Si muchos lo pasan en los primeros 1–2 segundos, deja de recomendarse. **El inicio lo decide todo.**
- Retención: que la gente vea el video completo (y lo repita). Duración de 30 s a **1:15 como máximo**: la decide el tema. Si la historia da para más, úsala; si no, córtala. Cada segundo extra debe aportar un dato o un giro nuevo, nunca relleno.
- Comentarios: valen más que un "suscríbete". Cierra con una pregunta fácil de responder.
- Datos reales (23-nov): en Instagram el 53 % pasaba el video en los primeros 3 s. Hay que mejorar el gancho.

## 1. Tema
Lee `topics.md`. Elige una curiosidad NUEVA (ni el mismo dato contado de otra forma) que cumpla las 3 pruebas:
1. **¿Le importa a cualquiera?** Algo que toca su vida, su cuerpo, su casa, su comida o algo que ve todos los días. Evita temas de nicho o muy técnicos.
2. **¿Rompe lo que la gente cree?** Un "no es lo que crees", un número absurdo, una comparación imposible o un "¿por qué…?" que todos se han preguntado.
3. **¿Se puede mostrar?** Debe poder dibujarse con animaciones claras (comparaciones, contadores, antes/después, mapas, diagramas).

Rota las categorías (no repitas la misma categoría dos videos seguidos; mira las últimas líneas de `topics.md`):
- Cuerpo humano y mente (por qué pasa X en tu cuerpo, sueño, sentidos, hábitos)
- Animales (superpoderes, récords, comportamientos raros)
- Espacio y planeta Tierra (escalas, clima extremo, océano, volcanes)
- Comida y cosas de casa (de dónde viene, por qué funciona, mitos)
- Historia y misterios (inventos por accidente, datos que no enseñan en la escuela)
- Tecnología, física y "cómo funciona" (objetos cotidianos, internet, aviones)
- Dinero, récords y comparaciones de escala

Si ya hay datos en Metricool (paso 6), favorece las categorías y tipos de gancho que tuvieron mejor retención y menos gente que pasó el video.

Verifica cada dato con búsqueda web en fuentes confiables (Smithsonian, Live Science, National Geographic, NASA, universidades, revistas científicas). Si un dato es dudoso o es un mito, no lo uses.

## 2. Guion (30–75 s, ≈85–200 palabras; nunca más de 1:15)
- **Primera frase = gancho (máx. 1,5 s, ≤ 10 palabras).** Arranca directo con el dato o la pregunta: "Tu cuerpo brilla en la oscuridad.", "Nunca has visto tu verdadera cara.". Nada de "Hola", "¿Sabías que…?" ni presentaciones.
- Después 2–5 datos explicados simple, cada uno con un mini giro ("pero eso no es lo más raro…") para que no se vayan. En videos de más de 45 s, pon un nuevo giro o revelación cada 8–10 s.
- Remate con el dato más fuerte al final, no al principio.
- Cierre (una frase): pregunta para comentarios + seguir. Ej.: "¿Lo sabías? Comenta, y sigue a LogiDatos para más."
- Español latino neutro, frases cortas, nada de relleno.

## 3. Voz (ElevenLabs, conector)
- `creative_create_flow` (nombre "LogiDatos #N – tema").
- `creative_generate_speech`: `voice_id = dlGxemPxFMTY7iXagmOj` (Fernando Martínez), `model_id = eleven_v4`, `generations_count = 1`, `flow_id` del paso anterior.
- Espera con `creative_get_flow_run_status` y toma el `content_url` del mp3.
- Fija la toma con `creative_add_flow_asset_node` (modality audio, generation_id) y transcribe con `creative_transcribe_audio` (`model_id eleven_scribe_v1`, `connect_from` = ese nodo). Da tiempos por palabra.
- Descarga con `curl` el mp3 y el `words_download_url`.
- Recorta el silencio inicial: la voz debe empezar antes de 0,2 s.
- ElevenLabs SOLO para la voz. NO generar video, imágenes ni música con IA.

## 4. Video (dibujado en código, calidad completa)
- `pip install --break-system-packages pycairo` si falta. Usa `pipeline/ejemplo_01_pulpo.py` (o `pipeline/video_02_venus.py`) como plantilla: fondo, subtítulos palabra por palabra (amarillo #FFD23F en la palabra activa), etiqueta LogiDatos arriba, tarjeta final con logo + "SÍGUENOS".
- **Primer cuadro (t = 0):** ya debe verse el texto del gancho en grande (≤ 6 palabras) y una imagen en movimiento. Nada de logo, intro ni fundido desde negro.
- Cambia de escena o de animación cada 2–4 s (zoom, contador, flecha, aparición). Una escena por idea, sincronizada con los tiempos de las palabras.
- Zona segura: nada importante debajo de y = 1560 salvo subtítulos, ni a la derecha (x > 960) entre y = 900 y 1700 (botones de las apps).
- **Formato final obligatorio: 1080×1920, 30 fps, H.264 CRF 18 preset veryfast, yuv420p, audio AAC 192k, `-movflags +faststart`.** Nunca bajar a 720p ni recomprimir para ahorrar peso (GitHub acepta archivos de hasta 100 MB; uno de 75 s pesa ~15–30 MB).
- **Música de fondo (obligatoria):** solo música ORIGINAL generada con `pipeline/musica.py` (sintetizada en código, sin copyright). Nunca descargues música ni la generes con IA.
  - Preset según el tema: `espacio` (espacio, planetas, océano profundo), `curioso` (animales, cuerpo humano, comida, casa), `misterio` (historia, misterios, récords), `energia` (tecnología, física, inventos, deportes). `--seed` = número del video.
  - `python3 pipeline/musica.py gen --dur <TOTAL> --preset <preset> --seed <N> --out build/musica.wav`
  - Mezcla: `python3 pipeline/musica.py mix build/silent.mp4 dl/voz.mp3 build/musica.wav <FINAL>.mp4 --total <TOTAL>`
  - Verifica con `ffmpeg -af volumedetect` que el volumen medio quede entre -18 y -14 dB y el máximo por debajo de -1 dB.
- Antes del render completo, revisa 6–8 cuadros de vista previa (incluye t = 0 y la tarjeta final) y corrige textos cortados, solapes y glifos que falten.
- Al final comprueba con `ffprobe` que el archivo sea 1080×1920 y dure 75 s o menos (TikTok, Instagram y YouTube Shorts lo aceptan sin problema).
- Nombre: `LogiDatos_NN_tema_corto.mp4`. Guarda el script del episodio como `pipeline/video_NN_tema.py`.

## 5. Publicación
- Rama `videos`: copia el mp4 a `videos/`, agrega el script a `pipeline/`, agrega la línea en `topics.md`, commit y push.
- Enlace público: `https://raw.githubusercontent.com/Oscar-Perez2/logidatos-videos/videos/videos/<archivo>.mp4`
- Metricool `createScheduledPost`: `blogId 8288543`, `autoPublish true`, `media` = enlace anterior, zona horaria America/Santo_Domingo. Siempre las CUATRO redes: `providers` = youtube, facebook, instagram, tiktok.
  - `youtubeData` = {title (≤ 70 caracteres, el gancho + " #shorts"), type "short", privacy "public", tags (6–8), category "EDUCATION", madeForKids false, isAiGeneratedContent false}
  - `facebookData` = {type "REEL", title = el mismo título sin "#shorts"}
  - `instagramData` = {type "REEL", showReelOnFeed true, isAiGenerated false}
  - `tiktokData` = {privacyOption "PUBLIC_TO_EVERYONE", title = el mismo título sin "#shorts"}
  - `text` = 2–3 frases con el dato + una pregunta para comentar + "🔔 Sigue a LogiDatos para más curiosidades en menos de un minuto." + 3–4 hashtags (#curiosidades #sabiasque + 1–2 del tema).
- Título: el gancho, no una descripción. Bien: "Tu cuerpo brilla en la oscuridad 😳". Mal: "Datos sobre la bioluminiscencia humana".
- Horario fijo: la corrida es a las 8:37 y el video se publica a las **19:00** del mismo día (America/Santo_Domingo), la hora pico de la audiencia. Si ya hay algo a esa hora (getScheduledPosts), usa la siguiente hora libre.

## 6. Aprender de los números (cada corrida, 1 minuto)
Antes de elegir el tema, consulta en Metricool (`getAnalyticsDataByMetrics`, brandId 8288543, últimos 14 días):
- YouTube: YTVP17 título, YTVP06 vistas, YTVP08 duración media vista.
- Instagram: IGRE06 enlace, IGRE23 vistas, IGRE24 tiempo medio, IGRE30 % que pasó el video en 3 s.
- TikTok: TKPO03 enlace, TKPO07 vistas, TKPO13 % que lo vio completo.
- Facebook: FBRE06 enlace, FBRE10 vistas, FBRE13 tiempo medio.
Si faltan datos, sigue igual. Si hay, repite lo que funcionó (categoría, tipo de gancho, duración) y evita lo que no.
