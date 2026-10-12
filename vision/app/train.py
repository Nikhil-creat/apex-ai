"""Train on ImageFolder data: data/<label>/*.jpg, then export ONNX."""
import torch, torch.nn as nn
from torchvision import datasets, transforms
from .cnn_service import ApexCNN, LABELS, export

def main(root="data", epochs=10):
    tf = transforms.Compose([transforms.Resize((224, 224)), transforms.ToTensor()])
    ds = datasets.ImageFolder(root, tf); assert ds.classes == sorted(LABELS) or ds.classes == LABELS, ds.classes
    dl = torch.utils.data.DataLoader(ds, batch_size=32, shuffle=True)
    m, opt = ApexCNN(len(ds.classes)), None
    opt = torch.optim.AdamW(m.parameters(), 1e-3)
    for e in range(epochs):
        for x, y in dl:
            opt.zero_grad(); loss = nn.functional.cross_entropy(m(x), y); loss.backward(); opt.step()
        print(e, float(loss))
    torch.save(m.state_dict(), "apex_cnn.pt"); export(weights="apex_cnn.pt")
if __name__ == "__main__": main()
