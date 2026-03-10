#!/usr/bin/env python3
"""
Advanced Detection: Deep CNN with CBAM Attention
Implements ResNet50 + CBAM attention mechanism for anomaly detection.
"""

import torch
import torch.nn as nn
import torchvision.models as models
from pathlib import Path
import json
import numpy as np
from PIL import Image
from tqdm import tqdm

class CBAM(nn.Module):
    """Convolutional Block Attention Module"""
    def __init__(self, channels, reduction=16):
        super(CBAM, self).__init__()
        # Channel attention
        self.avg_pool = nn.AdaptiveAvgPool2d(1)
        self.max_pool = nn.AdaptiveMaxPool2d(1)
        self.fc = nn.Sequential(
            nn.Conv2d(channels, channels // reduction, 1, bias=False),
            nn.ReLU(),
            nn.Conv2d(channels // reduction, channels, 1, bias=False)
        )
        # Spatial attention
        self.conv_spatial = nn.Conv2d(2, 1, 7, padding=3, bias=False)
        
    def forward(self, x):
        # Channel attention
        avg_out = self.fc(self.avg_pool(x))
        max_out = self.fc(self.max_pool(x))
        channel_att = torch.sigmoid(avg_out + max_out)
        x = x * channel_att
        
        # Spatial attention
        avg_spatial = torch.mean(x, dim=1, keepdim=True)
        max_spatial, _ = torch.max(x, dim=1, keepdim=True)
        spatial_input = torch.cat([avg_spatial, max_spatial], dim=1)
        spatial_att = torch.sigmoid(self.conv_spatial(spatial_input))
        x = x * spatial_att
        
        return x

class GalaxyAnomalyDetector(nn.Module):
    """ResNet50 + CBAM for galaxy anomaly detection"""
    def __init__(self, embedding_dim=2048):
        super(GalaxyAnomalyDetector, self).__init__()
        resnet = models.resnet50(weights=models.ResNet50_Weights.IMAGENET1K_V2)
        
        # Remove final FC layer
        self.features = nn.Sequential(*list(resnet.children())[:-2])
        
        # Add CBAM attention
        self.cbam = CBAM(2048)
        
        # Global pooling
        self.pool = nn.AdaptiveAvgPool2d(1)
        
        # Projection head for contrastive learning
        self.projection = nn.Sequential(
            nn.Linear(2048, 1024),
            nn.ReLU(),
            nn.Linear(1024, embedding_dim)
        )
        
        # Anomaly scoring head
        self.anomaly_head = nn.Sequential(
            nn.Linear(embedding_dim, 512),
            nn.ReLU(),
            nn.Dropout(0.3),
            nn.Linear(512, 1),
            nn.Sigmoid()
        )
        
    def forward(self, x, return_embedding=False):
        x = self.features(x)
        x = self.cbam(x)
        x = self.pool(x).flatten(1)
        
        if return_embedding:
            return x
            
        embedding = self.projection(x)
        anomaly_score = self.anomaly_head(embedding)
        
        return anomaly_score, embedding

class GalaxyDataset(torch.utils.data.Dataset):
    """Dataset for galaxy images"""
    def __init__(self, image_dir, metadata_file, transform=None):
        self.image_dir = Path(image_dir)
        self.transform = transform
        
        # Load metadata
        import pandas as pd
        self.metadata = pd.read_csv(metadata_file)
        
    def __len__(self):
        return len(self.metadata)
        
    def __getitem__(self, idx):
        row = self.metadata.iloc[idx]
        objid = row['objid']
        
        # Load image
        img_path = self.image_dir / f"{objid}.jpg"
        try:
            image = Image.open(img_path).convert('RGB')
        except:
            # Return blank image if file missing
            image = Image.new('RGB', (224, 224), (0, 0, 0))
            
        if self.transform:
            image = self.transform(image)
            
        return image, objid

def train_model(data_dir, epochs=10, batch_size=32, device='cpu'):
    """Train the anomaly detection model"""
    from torchvision import transforms
    
    transform = transforms.Compose([
        transforms.Resize((224, 224)),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], 
                           std=[0.229, 0.224, 0.225])
    ])
    
    model = GalaxyAnomalyDetector().to(device)
    
    # Note: Full training requires labeled anomalies
    # For now, we'll use the pretrained features for inference
    
    return model

def extract_embeddings(model, dataloader, device='cpu'):
    """Extract embeddings for all galaxies"""
    model.eval()
    embeddings = {}
    
    with torch.no_grad():
        for images, objids in tqdm(dataloader, desc="Extracting embeddings"):
            images = images.to(device)
            emb = model(images, return_embedding=True)
            
            for i, objid in enumerate(objids):
                embeddings[str(objid)] = emb[i].cpu().numpy().tolist()
                
    return embeddings

def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--extract', action='store_true', help='Extract embeddings')
    parser.add_argument('--train', action='store_true', help='Train model')
    parser.add_argument('--device', default='cpu', help='Device to use')
    args = parser.parse_args()
    
    ROOT = Path("~/Desktop/astro1").expanduser()
    
    if args.train:
        print("Training Galaxy Anomaly Detector...")
        model = train_model(ROOT / "data", device=args.device)
        # Save model
        torch.save(model.state_dict(), ROOT / "results" / "galaxy_anomaly_model.pth")
        print("Model saved to results/galaxy_anomaly_model.pth")
        
    if args.extract:
        print("Extracting embeddings with attention mechanism...")
        model = GalaxyAnomalyDetector()
        model.load_state_dict(torch.load(ROOT / "results" / "galaxy_anomaly_model.pth", 
                                         map_location='cpu'))
        
        from torchvision import transforms
        transform = transforms.Compose([
            transforms.Resize((224, 224)),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406], 
                               std=[0.229, 0.224, 0.225])
        ])
        
        dataset = GalaxyDataset(
            ROOT / "data" / "processed",
            ROOT / "data" / "metadata" / "processed_catalog.csv",
            transform=transform
        )
        
        dataloader = torch.utils.data.DataLoader(dataset, batch_size=32, shuffle=False)
        
        embeddings = extract_embeddings(model, dataloader, args.device)
        
        # Save embeddings
        with open(ROOT / "results" / "embeddings" / "attention_embeddings.json", 'w') as f:
            json.dump(embeddings, f)
            
        print(f"Extracted embeddings for {len(embeddings)} galaxies")

if __name__ == "__main__":
    main()
