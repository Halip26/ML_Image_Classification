# -*- coding: utf-8 -*-
"""Final_Project_Image_Classification_Model_Deployment.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1Nwe73NtrpuW8lgMgcy3ZivBmJpu8hlsW
"""

!pip install -q kaggle

import shutil
import sklearn
import tensorflow as tf
import matplotlib.pyplot as plt
from tensorflow.keras.preprocessing.image import ImageDataGenerator
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Conv2D, MaxPooling2D, Dropout, Flatten, Dense, BatchNormalization
from tensorflow.keras.optimizers import Adam
from tensorflow.keras.callbacks import ModelCheckpoint, EarlyStopping, ReduceLROnPlateau

from google.colab import files

uploaded = files.upload()

for fn in uploaded.keys():
    print('User uploaded file "{name}" with length {length} bytes'.format(
        name=fn, length=len(uploaded[fn])))

!mkdir -p ~/.kaggle
!mv kaggle.json ~/.kaggle/
!chmod 600 /root/.kaggle/kaggle.json

!kaggle datasets download -d trolukovich/apparel-images-dataset

import zipfile
import os

with zipfile.ZipFile("apparel-images-dataset.zip", "r") as zip_ref:
    zip_ref.extractall("apparel-images-dataset")

# memverifikasi bahwa file telah diekstrak
base_dir = 'apparel-images-dataset'
print(os.listdir(base_dir))

# fungsi menghitung jumlah data untuk setiap kelas
def count_data(directory):
    return len(os.listdir(directory))

classes = ['blue_pants', 'white_shoes', 'white_dress', 'blue_shorts', 'blue_shirt', 'blue_shoes', 'red_pants', 'black_pants', 'brown_shoes', 'white_pants', 'black_shorts', 'white_shorts', 'green_shirt', 'black_shoes', 'black_dress', 'green_shorts', 'blue_dress', 'black_shirt', 'red_shoes', 'green_pants', 'green_shoes', 'brown_pants', 'brown_shorts', 'red_dress']
totals = {cls: count_data(os.path.join(base_dir, cls)) for cls in classes}

# mencetak jumlah data untuk setiap kelas
for cls, total in totals.items():
    print(f"Total Data {cls} Image: {total}")

# generator untuk augmentasi gambar & data train/validasi
val_size = 0.2
image_size = (150, 150)

datagen = ImageDataGenerator(
    rotation_range=30,
    brightness_range=[0.2, 1.0],
    shear_range=0.2,
    zoom_range=0.2,
    horizontal_flip=True,
    fill_mode="nearest",
    rescale=1./255,
    validation_split=val_size
)

generator_params = dict(
    target_size=image_size,
    color_mode="rgb",
    class_mode="categorical",
    batch_size=128,
    shuffle=True
)

train_generator = datagen.flow_from_directory(
    base_dir,
    subset="training",
    classes=classes,
    **generator_params
)

val_generator = datagen.flow_from_directory(
    base_dir,
    subset="validation",
    classes=classes,
    **generator_params
)

# pembuatan model dengan output layer sesuai dengan jumlah kelas baru
num_classes = len(classes)

# pembuatan model image classification
model = Sequential([
    Conv2D(32, (3, 3), activation='relu', input_shape=(150, 150, 3)),
    BatchNormalization(),
    Conv2D(32, (3, 3), activation='relu', padding='same'),
    BatchNormalization(axis=3),
    MaxPooling2D(pool_size=(2, 2), padding='same'),
    Dropout(0.3),
    Conv2D(64, (3, 3), activation='relu', padding='same'),
    BatchNormalization(),
    Conv2D(64, (3, 3), activation='relu', padding='same'),
    BatchNormalization(axis=3),
    MaxPooling2D(pool_size=(2, 2), padding='same'),
    Dropout(0.3),
    Conv2D(128, (3, 3), activation='relu', padding='same'),
    BatchNormalization(),
    Conv2D(128, (3, 3), activation='relu', padding='same'),
    BatchNormalization(axis=3),
    MaxPooling2D(pool_size=(2, 2), padding='same'),
    Dropout(0.5),
    Flatten(),
    Dense(512, activation='relu'),
    BatchNormalization(),
    Dropout(0.5),
    Dense(128, activation='relu'),
    Dropout(0.25),
    Dense(num_classes, activation='softmax')
])

model.compile(optimizer='adam', loss='categorical_crossentropy', metrics=['accuracy'])
model.summary()

# penggunaan callbacks
models_dir = "saved_models"
if not os.path.exists(models_dir):
    os.makedirs(models_dir)

checkpointer = ModelCheckpoint(filepath='saved_models/model_vanilla.hdf5',
                               monitor='val_accuracy', mode='max',
                               verbose=1, save_best_only=True)
early_stopping = EarlyStopping(monitor='val_loss', mode='min', verbose=1, patience=3)
reduce_lr = ReduceLROnPlateau(monitor='val_loss', factor=0.2, patience=2, min_lr=0.001)
callbacks = [early_stopping, reduce_lr, checkpointer]

# melatih model
history = model.fit(train_generator, epochs=20, validation_data=val_generator, callbacks=callbacks)

# membuat visualisasi plot accuracy
plt.plot(history.history['accuracy'])
plt.plot(history.history['val_accuracy'])
plt.title('Accuracy')
plt.ylabel('accuracy')
plt.xlabel('epoch')
plt.legend(['train', 'val'], loc='upper left')
plt.show()

# membuat visualisasi plot loss
plt.plot(history.history['loss'])
plt.plot(history.history['val_loss'])
plt.title('Loss')
plt.ylabel('loss')
plt.xlabel('epoch')
plt.legend(['train', 'val'], loc='upper left')
plt.show()

# menkonversi model ke format TFLite
converter = tf.lite.TFLiteConverter.from_keras_model(model)
tflite_model = converter.convert()

# menyimpan model TFLite
with tf.io.gfile.GFile('model.tflite', 'wb') as f:
    f.write(tflite_model)