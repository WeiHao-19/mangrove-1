from keras.applications.vgg16 import VGG16, preprocess_input
from keras.preprocessing import image
from keras.models import Model
from sklearn.preprocessing import LabelEncoder, StandardScaler
import joblib
import numpy as np
import os
import argparse

class CNNFeatureExtractor:
    '''
    Class to represent a CNN-based feature extractor. This abstracts all the details of the CNN away from the classifier.
    '''
    def __init__(self, shape=(256, 256, 3), layer=None):
        '''
        Initializes a CNNFeatureExtractor using the VGG16 CNN.

        Arguments:
            shape: the shape of the imput images
        '''
        if layer is None:
            self.model = VGG16(weights='imagenet', include_top=False, pooling='avg', input_shape=shape)
        else:
            full_model = VGG16(weights='imagenet', include_top=False, pooling='avg', input_shape=shape)
            self.model = Model(inputs=full_model.input, outputs=full_model.get_layer(layer).output)
    
    def extract(self, img):
        '''
        Uses the CNN to extract a feature vector from an image.

        Arguments:
            img: an image in array form. Must be the same shape as specified in the constructor.
        
        Returns:
            np.array: the feature vector, with shape (1, n), where n is the length of the CNN output
        '''
        img = preprocess_input(img)
        if len(img.shape)==3:
            img = np.expand_dims(img, axis=0)
        feature = self.model.predict(img)
        return feature


if __name__=='__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-n', '--nbatches', type=int, help='the number of batches per directory', default=512)
    parser.add_argument('-b', '--batchsize', type=int, default=30, help='images per batch')
    parser.add_argument('--layer', help='the layer name to use (default last)')
    parser.add_argument('-i', '--input', help='input directory')
    parser.add_argument('-o', '--output', help='output directory')
    args = parser.parse_args()

    extractor = CNNFeatureExtractor(layer='block2_pool')
    train_path = os.path.abspath(args.input)
    out_path = os.path.abspath(args.output)
    train_labels = os.listdir(train_path)
    batchsize = args.batchsize
    labels = []
    images_per_dir = batchsize*args.nbatches

    features = []
    dirnum = 0      # directory number, 0 indexed
    for d in train_labels:
        files = os.listdir(os.path.join(train_path, d))
        j = 0       # number of image in batch, 1 indexed
        i = 0       # number of image in directory, 1 indexed
        batch = []
        fnames = []
        dir_features = np.zeros((min(len(files), images_per_dir), 512))
        for f in files:
            j += 1
            i += 1
            imfile = os.path.join(train_path, d, f)
            img = image.load_img(imfile)
            img = image.img_to_array(img)
            batch.append(img)
            labels.append(d)
            if j == batchsize or i == len(files):
                batch = np.array(batch)
                print(i)
                dir_features[i-batch.shape[0]:i] = extractor.extract(batch)
                # dir_features[i-batch.shape[0]:i] = np.ones((batch.shape[0], 512))
                batch = []
                j = 0
            if i==images_per_dir:
                break
        dirnum += 1
        features.append(dir_features)
    
    features = np.vstack(features)
    le = LabelEncoder()
    labels = le.fit_transform(labels)
    sc = StandardScaler()
    features = sc.fit_transform(features)
    print('[STATUS] Saving data...')
    np.save(os.path.join(out_path, 'features.npy'), features)
    np.save(os.path.join(out_path, 'labels.npy'), labels)
    print('[STATUS] Saving scaler and label encoder...')
    joblib.dump(le, os.path.join(out_path, 'le.joblib'))
    joblib.dump(sc, os.path.join(out_path, 'sc.joblib'))