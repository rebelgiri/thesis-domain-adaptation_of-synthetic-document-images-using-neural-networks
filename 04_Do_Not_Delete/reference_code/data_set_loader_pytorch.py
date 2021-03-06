# Import Libraries
import torch
import torchvision
import torchvision.transforms as transforms


# Specify transforms using torchvision.transforms as transforms library
transformations = {
 'cyclegan': transforms.Compose([
    transforms.RandomHorizontalFlip(),
    transforms.Grayscale(),
    transforms.Resize([286,286]),
    transforms.RandomCrop([256,256]),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.5], std=[0.5])
]),

 'classifier': transforms.Compose([
    transforms.Grayscale(),
    transforms.Resize([256,256]),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.5], std=[0.5])
])

}


def cyclegan_data_set_loader(synthetic_document_images_path, real_document_images_path):
    
    synthetic_document_images_folder = torchvision.datasets.ImageFolder(
        root=synthetic_document_images_path,
        transform=transformations['cyclegan']
    )
    synthetic_document_images_data_set_loader = torch.utils.data.DataLoader(
        synthetic_document_images_folder,
        batch_size=1,
        shuffle=True
    )

    real_document_images_folder = torchvision.datasets.ImageFolder(
        root=real_document_images_path,
        transform=transformations['cyclegan']
    )
    real_document_images_data_set_loader = torch.utils.data.DataLoader(
        real_document_images_folder,
        batch_size=1,
        shuffle=True
    )


    return (synthetic_document_images_data_set_loader, real_document_images_data_set_loader)
    


def classifier_data_set_loader(classifier_training_data_set_path, classifier_test_data_set_path):

    classifier_training_images_folder = torchvision.datasets.ImageFolder(
        root=classifier_training_data_set_path,
        transform=transformations['classifier']
    )

    classifier_training_images_data_set_loader = torch.utils.data.DataLoader(
        classifier_training_images_folder,
        batch_size=10,
        num_workers=4,
        shuffle=True
    )

    classifier_test_images_folder = torchvision.datasets.ImageFolder(
        root=classifier_test_data_set_path,
        transform=transformations['classifier']
    )

    classifier_test_images_data_set_loader = torch.utils.data.DataLoader(
        classifier_test_images_folder,
        batch_size=1200, # we have 1162 test images
        num_workers=4,
        shuffle=True
    )

    return (classifier_training_images_data_set_loader, classifier_test_images_data_set_loader, 
    classifier_training_images_folder.classes)



