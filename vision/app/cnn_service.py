"""Custom CNN -> ONNX -> FastAPI. Train, export, then serve with onnxruntime."""
import io, numpy as np, torch, torch.nn as nn
from fastapi import FastAPI, UploadFile
from PIL import Image
LABELS = ["invoice", "id_card", "form", "photo", "other"]
THRESHOLD = 0.75

class Block(nn.Module):
    def __init__(s, i, o):
        super().__init__(); s.c = nn.Sequential(nn.Conv2d(i, o, 3, padding=1, bias=False), nn.BatchNorm2d(o), nn.ReLU(), nn.MaxPool2d(2))
        s.skip = nn.Conv2d(i, o, 1, stride=2)
    def forward(s, x): return s.c(x) + s.skip(x)

class ApexCNN(nn.Module):
    def __init__(s, n=len(LABELS)):
        super().__init__()
        s.f = nn.Sequential(Block(3, 32), Block(32, 64), Block(64, 128), Block(128, 256), nn.AdaptiveAvgPool2d(1), nn.Flatten())
        s.h = nn.Linear(256, n)
    def forward(s, x): return s.h(s.f(x))

def export(path="apex_cnn.onnx", weights=None):
    m = ApexCNN().eval()
    if weights: m.load_state_dict(torch.load(weights))
    torch.onnx.export(m, torch.randn(1, 3, 224, 224), path, input_names=["x"], output_names=["y"], dynamic_axes={"x": {0: "b"}})

app = FastAPI()
_sess = None
def sess():
    global _sess
    if _sess is None:
        import onnxruntime as ort
        _sess = ort.InferenceSession("apex_cnn.onnx", providers=["CPUExecutionProvider"])
    return _sess

@app.get("/health")
def health(): return {"ok": True}

@app.post("/classify")
async def classify(file: UploadFile):
    img = Image.open(io.BytesIO(await file.read())).convert("RGB").resize((224, 224))
    x = (np.asarray(img, dtype=np.float32) / 255.0).transpose(2, 0, 1)[None]
    logits = sess().run(None, {"x": x})[0][0]
    p = np.exp(logits - logits.max()); p /= p.sum()
    i = int(p.argmax())
    return {"label": LABELS[i], "confidence": float(p[i]), "escalate": bool(p[i] < THRESHOLD)}
