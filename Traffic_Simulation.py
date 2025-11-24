import random
import pygame

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


# --- 3. SEMAFORY (Polymorfismus) ---

class TrafficLight:
    """
    Základní třída pro semafor (Rozhraní).
    """
    def __init__(self, position):
        self.position = position
        self.is_green = True

    def update(self, dt, vehicles):
        """
        Metoda update nově přijímá i seznam vozidel,
        aby 'chytré' semafory mohly reagovat na provoz.
        """
        pass


class CyclicTrafficLight(TrafficLight):
    """
    Klasický semafor - přepíná časově, auta ignoruje.
    """
    def __init__(self, position, interval):
        super().__init__(position)
        self.interval = interval
        self.timer = 0.0

    def update(self, dt, vehicles):
        # Tento semafor seznam 'vehicles' ignoruje, řídí se jen časem
        self.timer += dt
        if self.timer >= self.interval:
            self.is_green = not self.is_green
            self.timer = 0.0
            state = "ZELENÁ" if self.is_green else "ČERVENÁ"
            print(f"Cyklický semafor ({self.position}m) přepnul na: {state}")


class SmartTrafficLight(TrafficLight):
    """
    Inteligentní semafor.
    Defaultně je červená. Zelenou pustí jen, když se blíží auto.
    """
    def __init__(self, position, detection_range=50.0):
        super().__init__(position)
        self.detection_range = detection_range # Jak daleko semafor "vidí"
        self.is_green = False # Šetříme energii, defaultně červená :)

    def update(self, dt, vehicles):
        # 1. Zjistíme, jestli je nějaké auto v zóně před semaforem
        car_detected = False
        
        for vehicle in vehicles:
            distance = self.position - vehicle.position
            # Auto je před semaforem (distance > 0) A zároveň v dosahu senzoru
            if 0 < distance <= self.detection_range:
                car_detected = True
                break # Stačí nám jedno auto, abychom pustili zelenou
        
        # 2. Reakce semaforu
        if car_detected and not self.is_green:
            self.is_green = True
            print(f"SmartSemafor ({self.position}m): Auto detekováno -> ZELENÁ")
        
        elif not car_detected and self.is_green:
            self.is_green = False
            print(f"SmartSemafor ({self.position}m): Prázdno -> ČERVENÁ")


# --- 4. SILNICE (Řízení simulace) ---

class Road:
    def __init__(self, length):
        self.length = length
        self.vehicles = []
        self.traffic_lights = []

    def add_vehicle(self, vehicle):
        self.vehicles.append(vehicle)

    def add_traffic_light(self, light):
        self.traffic_lights.append(light)

    def update(self, dt):
        # 1. Aktualizace semaforů
        # DŮLEŽITÉ: Posíláme semaforům seznam aut (self.vehicles)
        for light in self.traffic_lights:
            light.update(dt, self.vehicles)

        # 2. Logika zastavování na červenou (Zatím jednoduchá)
        for vehicle in self.vehicles:
            # Zkontrolujeme všechny semafory
            should_stop = False
            for light in self.traffic_lights:
                # Pokud je semafor blízko před autem a je červená
                distance = light.position - vehicle.position
                if 0 < distance < 10 and not light.is_green:
                    should_stop = True
                    break
            
            if should_stop:
                vehicle.stop()
            else:
                # Pokud není důvod stát, auto se rozjede (vrátíme mu rychlost)
                # Poznámka: Toto je zjednodušení, v plné verzi by auto mělo svou max_speed
                if vehicle.stopped:
                    vehicle.stopped = False
                    vehicle.speed = 20 # Reset rychlosti (zjednodušeno)
            
            # 3. Pohyb auta
            vehicle.move(dt)


# --- 5. VIZUALIZACE (Pygame) ---

class Visualizer:
    """
    Třída starající se o vykreslování simulace pomocí Pygame.
    Odděluje logiku (Road) od grafiky (Pygame).
    """
    def __init__(self, road, width=1200, height=400):
        self.road = road
        self.width = width
        self.height = height
        self.scale = 1  # 1 metr = 1 pixel
        
        # Inicializace Pygame
        pygame.init()
        self.screen = pygame.display.set_mode((self.width, self.height))
        pygame.display.set_caption("Dopravní Simulace - OOP Semestrální práce")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont("Arial", 16)

    def draw_road(self):
        # Nakreslíme šedý pruh jako silnici uprostřed okna
        road_y = self.height // 2 - 20
        pygame.draw.rect(self.screen, (50, 50, 50), (0, road_y, self.road.length, 40))
        
        # Čáry na silnici
        pygame.draw.line(self.screen, (255, 255, 255), (0, self.height // 2), (self.road.length, self.height // 2), 2)

    def draw_vehicles(self):
        road_y = self.height // 2
        
        for v in self.road.vehicles:
            # Převod pozice na pixely
            x = v.position * self.scale
            y = road_y + 7 # Aby auto jelo v pruhu
            
            # Barva auta (podle toho, jestli brzdí)
            color = (255, 0, 0) # Červená default
            if isinstance(v, Car): color = (0, 0, 255)   # Modré auto
            if isinstance(v, Truck): color = (0, 255, 0) # Zelený kamion
            if isinstance(v, Bus): color = (255, 255, 0)   # Žlutý autobus
            
            if v.stopped:
                color = (100, 0, 0) # Tmavá, když stojí
            
            # Vykreslení (obdélník)
            # pygame.Rect(x, y, šířka, výška)
            pygame.draw.rect(self.screen, color, (x, y, v.get_length() * self.scale, 10))

    def draw_lights(self):
        road_y = self.height // 2 + 30 # Semafor bude pod silnicí
        
        for light in self.road.traffic_lights:
            x = light.position * self.scale
            
            # Barva světla
            color = (0, 255, 0) if light.is_green else (255, 0, 0)
            
            # Kolečko semaforu
            pygame.draw.circle(self.screen, color, (int(x), road_y), 8)
            
            # Detekční zóna pro Smart Semafor (jen pro debug)
            if isinstance(light, SmartTrafficLight):
                 pygame.draw.circle(self.screen, (255, 255, 255), (int(x), road_y), 3, 1)

    def run(self):
        running = True
        dt = 0.016 # Cca 60 FPS
        
        while running:
            # 1. Zpracování vstupů (zavření okna)
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                # Zde můžeš přidat ovládání (např. mezerník pro pauzu)

            # 2. Aktualizace logiky simulace
            self.road.update(dt)

            # 3. Vykreslení
            self.screen.fill((30, 30, 30)) # Tmavé pozadí
            
            self.draw_road()
            self.draw_lights()
            self.draw_vehicles()
            
            # Výpis času
            time_text = self.font.render(f"Simulace běží...", True, (255, 255, 255))
            self.screen.blit(time_text, (10, 10))

            # Překlopení bufferu (zobrazení snímku)
            pygame.display.flip()
            
            # Čekání na další snímek
            self.clock.tick(60) # 60 FPS

        pygame.quit()

# --- SPUŠTĚNÍ ---

if __name__ == "__main__":
    # 1. Vytvoření logiky (Model)
    road = Road(1200) # Silnice dlouhá 1200m
    
    # Semafory
    road.add_traffic_light(CyclicTrafficLight(400, 4.0))      # Obyčejný na 400m
    road.add_traffic_light(SmartTrafficLight(900, 100.0))     # Chytrý na 900m
    
    # Auta
    road.add_vehicle(Car(50, 25))      # Rychlé auto
    road.add_vehicle(Truck(0, 15))     # Pomalý kamion
    road.add_vehicle(Bus(-100, 20))    # Autobus 

    # 2. Spuštění vizualizace (View/Controller)
    app = Visualizer(road)
    app.run()