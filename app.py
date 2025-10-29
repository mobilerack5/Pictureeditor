import os
import time
import gradio as gr
from PIL import Image, ImageEnhance, ImageFilter, ImageOps
import tempfile # <-- Ezt adjuk hozzá az ideiglenes fájlokhoz

print("Függőségek importálva.")

# === 3. Képszerkesztő segédfüggvények ===

def apply_slider_adjustments(base_image, brightness, contrast, saturation, sharpness, blur):
    """
    Ez a függvény alkalmazza az összes csúszka beállítását a képre.
    """
    if base_image is None:
        return None, gr.DownloadButton(visible=False)
    
    if not isinstance(base_image, Image.Image):
        try:
            base_image = Image.fromarray(base_image)
        except Exception as e:
            print(f"Hiba a kép konvertálásánál: {e}")
            return None, gr.DownloadButton(visible=False)

    img = base_image.copy()

    # 1. Fényerő
    if brightness != 1.0:
        enhancer = ImageEnhance.Brightness(img)
        img = enhancer.enhance(brightness)
    
    # 2. Kontraszt
    if contrast != 1.0:
        enhancer = ImageEnhance.Contrast(img)
        img = enhancer.enhance(contrast)

    # 3. Színmélység (Saturation)
    if saturation != 1.0:
        enhancer = ImageEnhance.Color(img)
        img = enhancer.enhance(saturation)

    # 4. Élesség
    if sharpness != 1.0:
        enhancer = ImageEnhance.Sharpness(img)
        img = enhancer.enhance(sharpness)
        
    # 5. Elmosás (Blur)
    if blur > 0:
        img = img.filter(ImageFilter.GaussianBlur(radius=blur))

    # === MENTÉS MÓDOSÍTÁSA RENDERHEZ ===
    # A képet egy ideiglenes fájlba mentjük, amit a Gradio átad a letöltéshez.
    # A Render törli ezt, miután "elalszik", de a letöltés működni fog.
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as temp_file:
            save_path = temp_file.name
            img.save(save_path)
        
        # Frissítjük a letöltő gombot az új fájl elérési útjával és láthatóvá tesszük
        return img, gr.DownloadButton(value=save_path, visible=True, label="Letöltés")
    except Exception as e:
        print(f"Hiba a kép mentésekor: {e}")
        return img, gr.DownloadButton(visible=False)


def apply_transform(current_image, operation):
    """
    Alkalmazza a transzformációs műveleteket (forgatás, tükrözés, szürkeárnyalat).
    """
    if current_image is None:
        return None
    
    if not isinstance(current_image, Image.Image):
        current_image = Image.fromarray(current_image)
    
    img = current_image.copy()

    if operation == "rotate_right":
        img = img.rotate(-90, expand=True)
    elif operation == "flip_h":
        img = ImageOps.mirror(img)
    elif operation == "flip_v":
        img = ImageOps.flip(img)
    elif operation == "grayscale":
        img = ImageOps.grayscale(img)

    return img, img, 1.0, 1.0, 1.0, 1.0, 0.0


def reset_all_changes(original_image):
    """ Visszaállít mindent az eredeti feltöltött képre. """
    if original_image is None:
        return None, None, gr.DownloadButton(visible=False), 1.0, 1.0, 1.0, 1.0, 0.0
    
    return original_image, original_image, gr.DownloadButton(visible=False), 1.0, 1.0, 1.0, 1.0, 0.0


# === 4. A Gradio Felület (UI) ===
# (Ez pontosan ugyanaz, mint a Kaggle verziónál, csak a feltöltő gombból kivettem a 'clear' eseményt)

with gr.Blocks(theme=gr.themes.Soft(), title="Fotószerkesztő") as app:
    
    gr.Markdown("# 📸 Fotószerkesztő Alkalmazás (Render)")

    base_state = gr.State()
    original_state = gr.State()

    with gr.Row():
        with gr.Column(scale=1):
            
            upload_button = gr.Image(
                label="Kép feltöltése",
                type="pil"
            )
            
            with gr.Tabs():
                with gr.TabItem("🎨 Alapbeállítások"):
                    brightness_slider = gr.Slider(minimum=0.0, maximum=3.0, value=1.0, step=0.05, label="Fényerő", info="1.0 = Eredeti")
                    contrast_slider = gr.Slider(minimum=0.0, maximum=3.0, value=1.0, step=0.05, label="Kontraszt", info="1.0 = Eredeti")
                    saturation_slider = gr.Slider(minimum=0.0, maximum=3.0, value=1.0, step=0.05, label="Színmélység", info="1.0 = Eredeti")
                    sharpness_slider = gr.Slider(minimum=-2.0, maximum=5.0, value=1.0, step=0.1, label="Élesség", info="1.0 = Eredeti")
                    blur_slider = gr.Slider(minimum=0.0, maximum=10.0, value=0.0, step=0.2, label="Elmosás (Blur)")

                with gr.TabItem("🔄 Átalakítás és Szűrők"):
                    gr.Markdown("Figyelem: Ezek a műveletek véglegesen módosítják az aktuális képet.")
                    with gr.Row():
                        rotate_btn = gr.Button(value="Forgatás 90° (Jobbra) ↪️")
                        flip_h_btn = gr.Button(value="Vízszintes tükrözés ↔️")
                        flip_v_btn = gr.Button(value="Függőleges tükrözés ↕️")
                    with gr.Row():
                        grayscale_btn = gr.Button(value="Szürkeárnyalatos 🔳")
            
            with gr.Row():
                reset_button = gr.Button(value="Visszaállítás (Eredeti kép)", variant="stop")

        with gr.Column(scale=2):
            output_image = gr.Image(
                label="Szerkesztett kép",
                interactive=False,
                height=600
            )
            
            download_button = gr.DownloadButton(
                label="Letöltés",
                visible=False
            )

    # === 5. Eseménykezelők ===
    sliders = [brightness_slider, contrast_slider, saturation_slider, sharpness_slider, blur_slider]

    for slider in sliders:
        slider.release(
            fn=apply_slider_adjustments,
            inputs=[base_state] + sliders,
            outputs=[output_image, download_button]
        )

    upload_button.upload(
        fn=lambda img: (img, img, img, gr.DownloadButton(visible=False)),
        inputs=[upload_button],
        outputs=[output_image, base_state, original_state, download_button]
    )
    
    rotate_btn.click(
        fn=apply_transform,
        inputs=[output_image, gr.State("rotate_right")],
        outputs=[output_image, base_state] + sliders
    )
    
    flip_h_btn.click(
        fn=apply_transform,
        inputs=[output_image, gr.State("flip_h")],
        outputs=[output_image, base_state] + sliders
    )
    
    flip_v_btn.click(
        fn=apply_transform,
        inputs=[output_image, gr.State("flip_v")],
        outputs=[output_image, base_state] + sliders
    )
    
    grayscale_btn.click(
        fn=apply_transform,
        inputs=[output_image, gr.State("grayscale")],
        outputs=[output_image, base_state] + sliders
    )

    reset_button.click(
        fn=reset_all_changes,
        inputs=[original_state],
        outputs=[output_image, base_state, download_button] + sliders
    )


# === 6. Alkalmazás indítása RENDERHEZ ===
print("Alkalmazás indítása...")
# A Render a 'PORT' környezeti változóban adja meg, hogy melyik porton kell figyelni.
# A server_name="0.0.0.0" kulcsfontosságú, hogy a Docker konténeren kívülről is elérhető legyen.
port = int(os.environ.get("PORT", 7860))
app.launch(server_name="0.0.0.0", server_port=port)

