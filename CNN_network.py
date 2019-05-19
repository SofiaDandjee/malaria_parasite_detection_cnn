# -*- coding: utf-8 -*-
"""

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1V350SP7kaKt71uNeGO33ezYrfulc_pyp
"""

! git clone https://github.com/SofiaDandjee/data

# Libraries

import numpy as np
import torch
from torchvision import transforms, datasets
from torch.utils import data
from torch.utils.data.sampler import SubsetRandomSampler
from torch.utils.data import DataLoader
import torchvision
import matplotlib.pyplot as plt
import numpy as np
import torch.nn as nn
import torch.nn.functional as F
import torch.optim as optim
import random
from torch.optim.lr_scheduler import ReduceLROnPlateau
import os

filepath = 'data/cell_images/'


np.random.seed(40)

pathdir = os.listdir(filepath)
infdir = os.listdir(filepath + 'Parasitized')
uninfdir = os.listdir(filepath + '')
print(pathdir)

device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")

# Check if CPU available
print(torch.cuda.is_available())

#define transform to the data (data augmentation)
dataset_transform = transforms.Compose(
       [transforms.Resize((100,100)),
        transforms.ColorJitter(hue=0.05, saturation=0.05),
        transforms.RandomHorizontalFlip(),
        transforms.RandomVerticalFlip(),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.5295, 0.4239, 0.4530],
                             std=[0.3257, 0.2623, 0.2767])
    ])

#import data from gitHub repository
dataset = datasets.ImageFolder(root='data/cell_images/',transform=dataset_transform)


#define training, validation, test set sizes
n = len(dataset)
n_val = int(n*0.15)  #nb of val images
n_test = int(n*0.15) #nb of test images
n_train = n-n_val-n_test #nb of test images

train_set, val_set, test_set = data.random_split(dataset, (n_train, n_val, n_test))

#define training, validation, test loaders
train_loader = torch.utils.data.DataLoader(train_set, batch_size=32, shuffle=True, num_workers=0)
val_loader = torch.utils.data.DataLoader(val_set, batch_size=32, shuffle=False, num_workers=0)
test_loader = torch.utils.data.DataLoader(test_set, batch_size=32,shuffle=False, num_workers=0)


#define classes
classes=("Parasitized","Uninfected")

def imshow(img):
    img = img / 2 + 0.5
    npimg = img.numpy()
    plt.imshow(np.transpose(npimg, (1, 2, 0)))
    plt.show()

# get some random training images
dataiter = iter(train_loader)
images, labels = dataiter.next()

# show examples of images
imshow(torchvision.utils.make_grid(images))
# print their labels
print(' '.join('%5s' % classes[labels[j]] for j in range(4)))

torch.backends.cudnn.benchmark = True
torch.backends.cudnn.deterministic = True

#define network architecture
class Net(nn.Module):
    def __init__(self):
        super(Net, self).__init__()
        
        #1st convolution layer
        self.conv_layer1=nn.Sequential(
        nn.Conv2d(3, 32, 3),
        nn.BatchNorm2d(32,eps=1e-05, momentum=0.1),
        nn.ReLU(),
        nn.MaxPool2d(2, 2)
        )
        
        #2nd convolution layer
        self.conv_layer2 = nn.Sequential(
        nn.Conv2d(32, 32, 3),
        nn.BatchNorm2d(32,eps=1e-05, momentum=0.1),
        nn.ReLU(),
        nn.MaxPool2d(2,2)
        )
        
        #3rd convolution layer
        self.conv_layer3 = nn.Sequential(
        nn.Conv2d(32, 64, 3),
        nn.BatchNorm2d(64,eps=1e-05, momentum=0.1),
        nn.ReLU(),
        nn.MaxPool2d(2, 2)
        )
        
        #Fully connected layers
        self.fc_layer = nn.Sequential(
        nn.Linear(64*10*10,64),
        nn.BatchNorm1d(64,eps=1e-05, momentum=0.1),
        #nn.Dropout(p=0.5),
        nn.ReLU(),
        nn.Linear(64,2),
        )
	#forward pass
    def forward(self, x):
        x = self.conv_layer1(x)
        x = self.conv_layer2(x)    
        x = self.conv_layer3(x)
        x = x.view(-1, 64*10*10)
        x = self.fc_layer(x)
        
        return x



net=Net()
#send net to GPU
net.to(device)

#cross entropy loss
criterion = nn.CrossEntropyLoss()

#stochastic gradient descent
optimizer = optim.SGD(net.parameters(), lr=1e-1, weight_decay = 1e-4, momentum=0.9, nesterov=True)

#scheduler to adjust learning rate
scheduler = ReduceLROnPlateau(optimizer, mode= 'min', factor=0.1, patience=1)

n_epochs = 30
for epoch in range(n_epochs):
    
    running_loss=0
    
    for i, data in enumerate(train_loader, 0):
		
        # get the batch inputs
        inputs, labels = data
        inputs = inputs.to(device)
        labels = labels.to(device)
        
        # zero the parameter gradients
        optimizer.zero_grad()

        # Forward pass
        outputs = net(inputs)
        
        #Backward pass
        loss = criterion(outputs, labels)
        loss.backward()
        
        #Optimizer update
        optimizer.step()
        
        #Batch loss
        running_loss += loss.item()
        
        # print statistics every epoch
        if i == 500:
            print('[%d, %5d] loss: %.3f' %(epoch + 1, i+1, running_loss/500))
            running_loss = 0
    
    #Scheduler update
    scheduler.step(running_loss)
                  
print('Finished Training')

#evaluation mode
net.cpu()
net.eval()

import numpy as np
from sklearn.metrics import roc_auc_score

#Training accuracy and ACU
total = 0
auc_total = 0
correct = 0
i = 0
with torch.no_grad():
    for data in train_loader:
        images, labels = data
        outputs = net(images)
        _, predicted = torch.max(outputs.data, 1)
        total += labels.size(0)
        correct += (predicted == labels).sum().item()
        auc = roc_auc_score(labels.numpy(), predicted.numpy())
        auc_total += auc
        i = i + 1
       
print('Accuracy of the network on the train images: %.2f %%' % (
    100 * correct / total))
print('AUC of the network on the train images: %.2f %%' % (
    100 * auc_total / i))


#Validation accuracy and ACU
correct = 0
total = 0
auc_total = 0
i = 0
with torch.no_grad():
    for data in val_loader:
        images, labels = data
        outputs = net(images)
        _, predicted = torch.max(outputs.data, 1)
        total += labels.size(0)
        correct += (predicted == labels).sum().item()
        auc = roc_auc_score(labels.numpy(), predicted.numpy())
        auc_total += auc
        i = i + 1
print('Accuracy of the network on the validation images: %.2f %%' % (
    100 * correct / total))
print('AUC of the network on the validation images: %.2f %%' % (
    100 * auc_total / i))

#Test accuracy and ACU
correct = 0
total = 0
auc_total = 0
i = 0
with torch.no_grad():
    for data in test_loader:
        images, labels = data
        outputs = net(images)
        _, predicted = torch.max(outputs.data, 1)
        total += labels.size(0)
        correct += (predicted == labels).sum().item()
        auc = roc_auc_score(labels.numpy(), predicted.numpy())
        auc_total += auc
print('Accuracy of the network on the test images: %.2f %%' % (
    100 * correct / total))
print('AUC of the network on the test images: %.2f %%' % (
    100 * auc_total / i))

#Validation confusion matrix
nb_classes = 2

confusion_matrix = torch.zeros(nb_classes, nb_classes)
with torch.no_grad():
    for i, (inputs, classes) in enumerate(val_loader):
        outputs = net(inputs)
        _, preds = torch.max(outputs, 1)
        for t, p in zip(classes.view(-1), preds.view(-1)):
                confusion_matrix[t.long(), p.long()] += 1

print(confusion_matrix)
