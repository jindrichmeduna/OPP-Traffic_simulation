import random

# --- 1. RODIČOVSKÉ TŘÍDY (Dědičnost) ---
class Vehicle:
    """
    Základní třída pro všechna vozidla.
    Ostatní auta (Car, Truck, Bus) z ní budou dědit.
    """
    def __init__(self, position, speed):
        self.position = position  # Pozice v metrech
        self.speed = speed        # Rychlost v m/s
        self.stopped = False      # Zda auto stojí
        self.color = "red"        # Jen pro vizualizaci

    def get_length(self):
        """Tuto metodu přepíšeme v potomcích (Car, Truck...)."""
        return 0.0

    def move(self, dt):
        """
        Fyzika pohybu.
        Pokud auto nestojí, posuneme ho.
        """
        if not self.stopped:
            # Dráha = rychlost * čas
            self.position += self.speed * dt

    def stop(self):
        self.stopped = True
        self.speed = 0


# --- 2. KONKRÉTNÍ AUTA ---

class Car(Vehicle):
    def get_length(self):
        return 4.5  # Osobák je nejkratší


class Bus(Vehicle):
    def get_length(self):
        return 10.0 # Autobus je střední délky


class Truck(Vehicle):
    def get_length(self):
        return 12.0 # Kamion je nejdelší


# --- 3. SEMAFORY ---

class TrafficLight:
    """
    Základní třída pro semafor.
    """
    def __init__(self, position):
        self.position = position
        self.is_green = True

    def update(self, dt):
        # Základní semafor nic nedělá, logiku přidáme v potomcích
        pass


class CyclicTrafficLight(TrafficLight):
    """
    Semafor, který se přepíná podle času.
    """
    def __init__(self, position, interval):
        # Voláme __init__ rodiče (TrafficLight), aby se nastavila pozice
        super().__init__(position)
        self.interval = interval
        self.timer = 0.0

    def update(self, dt):
        self.timer += dt
        if self.timer >= self.interval:
            self.is_green = not self.is_green # Přepnutí stavu
            self.timer = 0.0
            state = "ZELENÁ" if self.is_green else "ČERVENÁ"
            print(f"Semafor na {self.position}m přepnul na: {state}")