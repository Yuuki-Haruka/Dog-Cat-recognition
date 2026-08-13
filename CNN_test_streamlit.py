import streamlit as st
import numpy as np
import torch
import torch.nn as nn
import torchvision.models as models
from PIL import Image
@st.cache_resource
def load_model():
    cnn = models.resnet18(pretrained=False)
    for param in cnn.parameters():
        param.requires_grad = False
    for param in cnn.layer4.parameters():
        param.requires_grad = True
    cnn.fc = nn.Sequential(nn.Dropout(0.3), nn.Linear(cnn.fc.in_features, 2))
    cnn.load_state_dict(torch.load('catdog_cnn_weights.pth', map_location='cpu'))
    cnn.eval()
    return cnn
cnn_model = load_model()
mean = np.array([0.485, 0.456, 0.406], dtype=np.float32)
std  = np.array([0.229, 0.224, 0.225], dtype=np.float32)
st.title('Cat vs Dog Classifier')
uploaded = st.file_uploader('Upload an image', type=['jpg', 'jpeg', 'png'])
if uploaded:
    img = Image.open(uploaded).convert('RGB')
    st.image(img, caption='Uploaded image', width=200)
    img = img.resize((224, 224))
    x = np.array(img, dtype=np.float32) / 255.0
    x = (x - mean) / std
    x = x.transpose(2, 0, 1)
    x = torch.tensor(x, dtype=torch.float32).unsqueeze(0)
    with torch.no_grad():
        out = cnn_model(x)
    prob = torch.softmax(out, dim=1)[0]
    cat_prob = float(prob[0]) * 100
    dog_prob = float(prob[1]) * 100
    label = 'Cat' if cat_prob > dog_prob else 'Dog'
    st.subheader(f'Prediction: {label}')
    st.write(f'Cat: {cat_prob:.1f}%')
    st.progress(cat_prob / 100)
    st.write(f'Dog: {dog_prob:.1f}%')
    st.progress(dog_prob / 100)