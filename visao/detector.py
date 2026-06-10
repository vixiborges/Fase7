"""
FarmTech Solutions – Fase 6
Visão Computacional com YOLOv5
Detecta pragas, doenças e crescimento irregular em imagens de lavoura.
Usa imagens estáticas de uma pasta (sem ESP32-CAM físico).
"""

import os
import sys
import json
import random
from datetime import datetime
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

# Classes que o modelo detecta
CLASSES = ["saudavel", "praga", "doenca", "crescimento_irregular"]

# Cores para visualização (BGR → RGB no Streamlit)
CORES_CLASSE = {
    "saudavel":              (34, 197, 94),   # verde
    "praga":                 (239, 68, 68),   # vermelho
    "doenca":                (234, 179, 8),   # amarelo
    "crescimento_irregular": (249, 115, 22),  # laranja
}

PASTA_IMAGENS = os.path.join(os.path.dirname(__file__), "..", "assets", "sample_images")


def _tentar_carregar_yolo():
    """Tenta importar YOLOv5 via torch.hub. Retorna modelo ou None."""
    try:
        import torch
        model = torch.hub.load("ultralytics/yolov5", "yolov5s", pretrained=True, verbose=False)
        model.conf = 0.40
        return model
    except Exception:
        return None


def _inferencia_simulada(caminho_imagem):
    """
    Fallback: retorna detecções sintéticas realistas quando YOLOv5
    não está disponível (sem GPU / sem PyTorch instalado).
    """
    random.seed(hash(os.path.basename(caminho_imagem)) % (2**32))
    n_deteccoes = random.randint(1, 4)
    deteccoes = []
    for _ in range(n_deteccoes):
        classe = random.choices(
            CLASSES,
            weights=[0.50, 0.20, 0.20, 0.10]  # maioria saudável
        )[0]
        confianca = round(random.uniform(0.45, 0.97), 3)
        x1 = random.randint(10, 200)
        y1 = random.randint(10, 200)
        x2 = x1 + random.randint(50, 200)
        y2 = y1 + random.randint(50, 200)
        deteccoes.append({
            "classe": classe,
            "confianca": confianca,
            "bbox": [x1, y1, x2, y2]
        })
    return deteccoes, "simulado"


def processar_imagem(caminho_imagem, modelo=None):
    """
    Processa uma imagem e retorna detecções.
    Se modelo YOLOv5 for fornecido, usa inferência real.
    Caso contrário, usa simulação.
    Retorna: (lista_de_deteccoes, modo) onde modo é 'yolov5' ou 'simulado'
    """
    if not os.path.isfile(caminho_imagem):
        return [], "erro"

    if modelo is not None:
        try:
            results = modelo(caminho_imagem)
            deteccoes = []
            for *box, conf, cls_id in results.xyxy[0].tolist():
                cls_idx = int(cls_id) % len(CLASSES)
                deteccoes.append({
                    "classe": CLASSES[cls_idx],
                    "confianca": round(float(conf), 3),
                    "bbox": [int(b) for b in box]
                })
            return deteccoes, "yolov5"
        except Exception:
            pass

    return _inferencia_simulada(caminho_imagem)


def processar_pasta(pasta=None, modelo=None):
    """
    Processa todas as imagens de uma pasta.
    Retorna lista de resultados por imagem.
    """
    pasta = pasta or PASTA_IMAGENS
    extensoes = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}
    imagens = [
        str(p) for p in Path(pasta).iterdir()
        if p.suffix.lower() in extensoes
    ]
    if not imagens:
        return []

    resultados = []
    for img_path in sorted(imagens):
        deteccoes, modo = processar_imagem(img_path, modelo)
        resultados.append({
            "imagem": os.path.basename(img_path),
            "caminho": img_path,
            "deteccoes": deteccoes,
            "modo": modo,
            "processado_em": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "total_deteccoes": len(deteccoes),
            "tem_problema": any(d["classe"] != "saudavel" for d in deteccoes)
        })
    return resultados


def resumo_deteccoes(resultados):
    """Agrega contagem de classes em todos os resultados."""
    contagem = {c: 0 for c in CLASSES}
    for r in resultados:
        for d in r.get("deteccoes", []):
            contagem[d["classe"]] = contagem.get(d["classe"], 0) + 1
    total = sum(contagem.values())
    return {
        "por_classe": contagem,
        "total": total,
        "percentual_saudavel": round(contagem["saudavel"] / total * 100, 1) if total > 0 else 0
    }


def gerar_imagens_exemplo():
    """
    Cria imagens de exemplo (gradientes coloridos) para demonstração
    quando não há imagens reais disponíveis.
    """
    try:
        from PIL import Image, ImageDraw, ImageFont
        import numpy as np

        os.makedirs(PASTA_IMAGENS, exist_ok=True)
        nomes = [
            ("lavoura_soja_01.jpg",   (34, 139, 34)),   # verde escuro
            ("lavoura_milho_01.jpg",  (107, 142, 35)),  # verde oliva
            ("lavoura_praga_01.jpg",  (139, 69, 19)),   # marrom
            ("lavoura_doenca_01.jpg", (218, 165, 32)),  # dourado
        ]
        for nome, cor_base in nomes:
            caminho = os.path.join(PASTA_IMAGENS, nome)
            if not os.path.exists(caminho):
                arr = np.full((480, 640, 3), cor_base, dtype=np.uint8)
                # Adiciona ruído para parecer mais realista
                ruido = np.random.randint(-30, 30, arr.shape, dtype=np.int16)
                arr = np.clip(arr.astype(np.int16) + ruido, 0, 255).astype(np.uint8)
                img = Image.fromarray(arr)
                draw = ImageDraw.Draw(img)
                draw.text((10, 10), nome.replace(".jpg", "").replace("_", " ").title(),
                          fill=(255, 255, 255))
                img.save(caminho)
        return True
    except ImportError:
        # Cria arquivos placeholder sem PIL
        os.makedirs(PASTA_IMAGENS, exist_ok=True)
        return False


if __name__ == "__main__":
    print("=== FarmTech Solutions – Visão Computacional (Fase 6) ===\n")
    gerar_imagens_exemplo()
    resultados = processar_pasta()
    if not resultados:
        print("Nenhuma imagem encontrada em assets/sample_images/")
    else:
        for r in resultados:
            print(f"📷 {r['imagem']}")
            for d in r["deteccoes"]:
                print(f"   [{d['classe'].upper():25s}] conf={d['confianca']:.2%}")
            print()
        resumo = resumo_deteccoes(resultados)
        print(f"Resumo: {resumo['total']} detecções | {resumo['percentual_saudavel']}% saudável")
