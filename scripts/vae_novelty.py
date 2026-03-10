#!/usr/bin/env python3
"""
Variational Autoencoder for Galaxy Novelty Detection
Uses reconstruction error as anomaly score.
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
from pathlib import Path
import json
import numpy as np
from PIL import Image
from tqdm import tqdm
import torchvision.transforms as transforms

class GalaxyVAE(nn.Module):
    """Variational Autoencoder for galaxy images"""
    def __init__(self, latent_dim=128, input_channels=3):
        super(GalaxyVAE, self).__init__()
        
        self.latent_dim = latent_dim
        
        # Encoder
        self.encoder = nn.Sequential(
            nn.Conv2d(input_channels, 32, 4, stride=2, padding=1),  # 112x112
            nn.ReLU(),
            nn.Conv2d(32, 64, 4, stride=2, padding=1),  # 56x56
            nn.ReLU(),
            nn.Conv2d(64, 128, 4, stride=2, padding=1),  # 28x28
            nn.ReLU(),
            nn.Conv2d(128, 256, 4, stride=2, padding=1),  # 14x14
            nn.ReLU(),
            nn.Conv2d(256, 512, 4, stride=2, padding=1),  # 7x7
            nn.ReLU(),
        )
        
        # Latent space
        self.fc_mu = nn.Linear(512 * 7 * 7, latent_dim)
        self.fc_logvar = nn.Linear(512 * 7 * 7, latent_dim)
        self.fc_decode = nn.Linear(latent_dim, 512 * 7 * 7)
        
        # Decoder
        self.decoder = nn.Sequential(
            nn.ConvTranspose2d(512, 256, 4, stride=2, padding=1),  # 14x14
            nn.ReLU(),
            nn.ConvTranspose2d(256, 128, 4, stride=2, padding=1),  # 28x28
            nn.ReLU(),
            nn.ConvTranspose2d(128, 64, 4, stride=2, padding=1),  # 56x56
            nn.ReLU(),
            nn.ConvTranspose2d(64, 32, 4, stride=2, padding=1),  # 112x112
            nn.ReLU(),
            nn.ConvTranspose2d(32, input_channels, 4, stride=2, padding=1),  # 224x224
            nn.Sigmoid()
        )
        
    def encode(self, x):
        x = self.encoder(x)
        x = x.view(x.size(0), -1)
        mu = self.fc_mu(x)
        logvar = self.fc_logvar(x)
        return mu, logvar
    
    def reparameterize(self, mu, logvar):
        std = torch.exp(0.5 * logvar)
        eps = torch.randn_like(std)
        return mu + eps * std
    
    def decode(self, z):
        x = self.fc_decode(z)
        x = x.view(x.size(0), 512, 7, 7)
        x = self.decoder(x)
        return x
    
    def forward(self, x):
        mu, logvar = self.encode(x)
        z = self.reparameterize(mu, logvar)
        recon_x = self.decode(z)
        return recon_x, mu, logvar
    
    def reconstruction_error(self, x):
        """Compute per-image reconstruction error"""
        with torch.no_grad():
            recon_x, _, _ = self.forward(x)
            error = F.mse_loss(recon_x, x, reduction='none').mean(dim=[1, 2, 3])
        return error

def vae_loss(recon_x, x, mu, logvar, kl_weight=1.0):
    """VAE loss = reconstruction + KL divergence"""
    recon_loss = F.mse_loss(recon_x, x, reduction='sum')
    kl_loss = -0.5 * torch.sum(1 + logvar - mu.pow(2) - logvar.exp())
    return recon_loss + kl_weight * kl_loss

class GalaxyImageDataset(torch.utils.data.Dataset):
    """Dataset for galaxy images"""
    def __init__(self, image_dir, metadata_file, transform=None):
        import pandas as pd
        self.image_dir = Path(image_dir)
        self.transform = transform
        self.metadata = pd.read_csv(metadata_file)
        
    def __len__(self):
        return len(self.metadata)
        
    def __getitem__(self, idx):
        row = self.metadata.iloc[idx]
        objid = str(row['objid'])  # Convert to string to avoid uint64 issues
        
        img_path = self.image_dir / f"{objid}.jpg"
        try:
            image = Image.open(img_path).convert('RGB')
        except:
            image = Image.new('RGB', (224, 224), (128, 128, 128))
            
        if self.transform:
            image = self.transform(image)
            
        return image, objid

def train_vae(data_dir, metadata_file, epochs=50, batch_size=32, 
              learning_rate=1e-3, device='cpu'):
    """Train VAE on galaxy images"""
    from torch.utils.data import DataLoader
    
    ROOT = Path("~/Desktop/astro1").expanduser()
    
    transform = transforms.Compose([
        transforms.Resize((224, 224)),
        transforms.ToTensor(),
    ])
    
    dataset = GalaxyImageDataset(data_dir, metadata_file, transform=transform)
    dataloader = DataLoader(dataset, batch_size=batch_size, shuffle=True, num_workers=0)
    
    model = GalaxyVAE(latent_dim=128).to(device)
    optimizer = torch.optim.Adam(model.parameters(), lr=learning_rate)
    
    print(f"Training VAE on {len(dataset)} galaxies...")
    
    for epoch in range(epochs):
        model.train()
        total_loss = 0
        
        for batch_idx, (images, objids) in enumerate(tqdm(dataloader, desc=f"Epoch {epoch+1}/{epochs}")):
            images = images.to(device)
            
            optimizer.zero_grad()
            recon_images, mu, logvar = model(images)
            loss = vae_loss(recon_images, images, mu, logvar)
            
            loss.backward()
            optimizer.step()
            
            total_loss += loss.item()
            
        avg_loss = total_loss / len(dataset)
        print(f"Epoch {epoch+1}: Average loss = {avg_loss:.4f}")
        
        # Save checkpoint every 10 epochs
        if (epoch + 1) % 10 == 0:
            checkpoint_path = ROOT / "results" / f"vae_checkpoint_epoch{epoch+1}.pth"
            torch.save({
                'epoch': epoch,
                'model_state_dict': model.state_dict(),
                'optimizer_state_dict': optimizer.state_dict(),
                'loss': avg_loss,
            }, checkpoint_path)
    
    # Save final model
    final_path = ROOT / "results" / "galaxy_vae_final.pth"
    torch.save(model.state_dict(), final_path)
    print(f"VAE model saved to {final_path}")
    
    return model

def detect_anomalies_vae(model, data_dir, metadata_file, threshold_percentile=99,
                         device='cpu'):
    """Detect anomalies using VAE reconstruction error"""
    from torch.utils.data import DataLoader
    
    transform = transforms.Compose([
        transforms.Resize((224, 224)),
        transforms.ToTensor(),
    ])
    
    dataset = GalaxyImageDataset(data_dir, metadata_file, transform=transform)
    dataloader = DataLoader(dataset, batch_size=32, shuffle=False)
    
    model.eval()
    
    all_errors = []
    all_objids = []
    
    with torch.no_grad():
        for images, objids in tqdm(dataloader, desc="Computing reconstruction errors"):
            images = images.to(device)
            errors = model.reconstruction_error(images)
            
            all_errors.extend(errors.cpu().numpy().tolist())
            all_objids.extend(objids)  # Already strings
    
    # Calculate threshold
    threshold = np.percentile(all_errors, threshold_percentile)
    
    # Create results
    results = []
    for objid, error in zip(all_objids, all_errors):
        results.append({
            'objid': objid,
            'reconstruction_error': float(error),
            'is_anomaly': bool(error > threshold),
            'anomaly_score': float(error / threshold)  # Normalized score
        })
    
    # Sort by error
    results.sort(key=lambda x: x['reconstruction_error'], reverse=True)
    
    return results, threshold

def main():
    import argparse
    parser = argparse.ArgumentParser(description='VAE-based anomaly detection')
    parser.add_argument('--train', action='store_true', help='Train VAE')
    parser.add_argument('--detect', action='store_true', help='Detect anomalies')
    parser.add_argument('--epochs', type=int, default=50, help='Training epochs')
    parser.add_argument('--batch-size', type=int, default=32, help='Batch size')
    parser.add_argument('--device', default='cpu', help='Device (cpu/cuda)')
    parser.add_argument('--threshold', type=int, default=99, 
                       help='Percentile threshold for anomalies')
    args = parser.parse_args()
    
    ROOT = Path("~/Desktop/astro1").expanduser()
    data_dir = ROOT / "data" / "processed"
    metadata_file = ROOT / "data" / "metadata" / "processed_catalog.csv"
    
    if args.train:
        model = train_vae(data_dir, metadata_file, 
                         epochs=args.epochs, 
                         batch_size=args.batch_size,
                         device=args.device)
        
    if args.detect:
        # Load trained model
        model = GalaxyVAE(latent_dim=128).to(args.device)
        model_path = ROOT / "results" / "galaxy_vae_final.pth"
        
        if not model_path.exists():
            print(f"Error: Model not found at {model_path}")
            print("Please train the model first with --train")
            return
            
        model.load_state_dict(torch.load(model_path, map_location=args.device))
        
        results, threshold = detect_anomalies_vae(
            model, data_dir, metadata_file,
            threshold_percentile=args.threshold,
            device=args.device
        )
        
        # Save results
        output_file = ROOT / "results" / "anomaly_scores" / "vae_anomalies.json"
        with open(output_file, 'w') as f:
            json.dump({
                'threshold': float(threshold),
                'total_galaxies': len(results),
                'anomalies_detected': sum(1 for r in results if r['is_anomaly']),
                'results': results
            }, f, indent=2)
            
        print(f"Detection complete. Found {sum(1 for r in results if r['is_anomaly'])} anomalies")
        print(f"Results saved to {output_file}")

if __name__ == "__main__":
    main()
