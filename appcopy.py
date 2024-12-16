import tensorflow as tf
import numpy as np
import matplotlib.pyplot as plt

# Gerar dados fictícios (y = 2x + 1 com ruído)
x = np.linspace(-1, 1, 100).reshape(-1, 1)
y = 2 * x + 1 + 0.2 * np.random.randn(*x.shape)

# Definir o modelo da rede neural
model = tf.keras.Sequential([
    tf.keras.layers.Dense(1, input_dim=1)  # Camada densa com 1 entrada e 1 saída
])

# Compilar o modelo
model.compile(optimizer='sgd', loss='mse')

# Treinar o modelo
model.fit(x, y, epochs=100, verbose=0)

# Resultados
predictions = model.predict(x)

# Visualizar os resultados
plt.scatter(x, y, label="Dados reais")
plt.plot(x, predictions, color='red', label="Previsão da Rede")
plt.title("Ajuste da Rede Neural")
plt.legend()
plt.show()

# Mostrar os pesos aprendidos
weights = model.get_weights()
print("Pesos aprendidos pela rede:", weights)
