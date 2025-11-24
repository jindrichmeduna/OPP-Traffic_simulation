import random
import pygame

# --- 1. RODIČOVSKÉ TŘÍDY (Dědičnost) ---
class Vehicle:
    """
    Základní třída pro všechna vozidla.
    Ostatní auta (Car, Truck, Bus) z ní budou dědit.
    """
    def __init__(self, position, speed, acceleration):
        self.position = position  # Pozice v metrech
        self.speed = speed        # Rychlost v m/s
        self.max_speed = speed    # Maximální rychlost pro opětovné rozjetí
        self.acceleration = acceleration
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


# --- 2. KONKRÉTNÍ VOZIDLA ---

class Car(Vehicle):
    def __init__(self, speed, position):
        super().__init__(position, speed, acceleration = 7.0)
        self.color = (0, 100, 255) # Modrá

    def get_length(self):
        return 10  # Osobák je nejkratší


class Bus(Vehicle):
    def __init__(self, speed, position):
        super().__init__(position, speed, acceleration = 5)
        self.color = (255, 255, 0) # Žlutá

    def get_length(self):
        return 20 # Autobus je střední délky


class Truck(Vehicle):
    def __init__(self, speed, position):
        super().__init__(position, speed, acceleration = 3)
        self.color = (0, 255, 0) # Zelená

    def get_length(self):
        return 30 # Kamion je nejdelší


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
    def __init__(self, length, direction = 'H', start_x=0, start_y=0):
        self.length = length
        self.direction = direction # 'H' = Horizontal, 'V' = Vertical
        self.start_x = start_x
        self.start_y = start_y
        self.vehicles = []       # Seznam vozidel
        self.traffic_lights = [] # Seznam semaforů

        self.stats_cars_finished = 0  # Počet aut, co dojela do cíle
        self.stats_avg_speed = 0.0    # Průměrná rychlost aut na silnici

    def add_vehicle(self, vehicle):
        self.vehicles.append(vehicle)

    def add_traffic_light(self, light):
        self.traffic_lights.append(light)

    def update(self, dt):
        # 1. Aktualizace semaforů
        for light in self.traffic_lights:
            light.update(dt, self.vehicles)

        # DŮLEŽITÉ: Seřadíme vozidla podle pozice (od nejvzdálenějšího po nejbližší)
        # Díky tomu přesně víme, že vehicles[i+1] je auto PŘED vehicles[i]
        self.vehicles.sort(key=lambda v: v.position)

        # 2. Hlavní smyčka pro každé vozidlo
        for i in range(len(self.vehicles)):
            vehicle = self.vehicles[i]
            
            # --- A) Resetování stavu a Akcelerace ---
            if vehicle.stopped:
                 # Pokud auto stojí (brzdí), nic neděláme, dokud nedostane pokyn k rozjezdu
                 pass 
            else:
                # Pokud auto jede pomaleji než je jeho maximálka, zrychlujeme
                if vehicle.speed < vehicle.max_speed:
                    # Vzorec: rychlost = rychlost + zrychlení * čas
                    vehicle.speed += vehicle.acceleration * dt
                    
                    # Pojistka: nesmíme překročit maximálku
                    if vehicle.speed > vehicle.max_speed:
                        vehicle.speed = vehicle.max_speed

            # --- B) Reakce na semafory ---
            should_stop_at_light = False
            for light in self.traffic_lights:
                distance = light.position - vehicle.position
                # Pokud je semafor blízko (méně než 10m) a je červená
                if 0 < distance < 10 and not light.is_green:
                    should_stop_at_light = True
                    break
            
            if should_stop_at_light:
                vehicle.stop()
            elif vehicle.stopped:
                # Pokud stálo, ale už je zelená, rozjedeme ho
                # Tady využíváme max_speed
                vehicle.stopped = False

            # --- C) Reakce na vozidla (Adaptivní tempomat) ---
            # Podíváme se, jestli je před námi nějaké auto
            # i + 1 je index auta před námi (protože jsme je seřadili)
            if i < len(self.vehicles) - 1:
                vehicle_ahead = self.vehicles[i+1]
                
                # Vypočítáme mezeru (od čumáku našeho auta k zadku auta před námi)
                # vehicle_ahead.get_length() je důležité, abychom do něj nevjeli polovinou
                gap = vehicle_ahead.position - vehicle.position - vehicle_ahead.get_length()
                
                # Bezpečná vzdálenost (např. 15 metrů)
                safe_distance = 20.0
                
                if gap < safe_distance:
                    # HROZÍ SRÁŽKA!
                    
                    if vehicle_ahead.stopped or vehicle_ahead.speed == 0:
                        # Pokud auto před námi stojí a jsme fakt blízko -> Zastavíme taky
                        if gap < 5.0: # 2 metry od nárazníku
                            vehicle.stop()
                        else:
                            # Dojíždíme ho, zpomalíme drasticky na 10 m/s
                            vehicle.speed = min(vehicle.speed, 10.0) 
                    else:
                        # Auto před námi jede, ale pomaleji -> přizpůsobíme rychlost
                        # Jedeme max tak rychle, jako auto před námi
                        if vehicle.speed > vehicle_ahead.speed:
                            vehicle.speed = vehicle_ahead.speed

            # 3. Aplikace pohybu
            vehicle.move(dt)

        # --- 4. Odstranění aut a aktualizace statistik ---
        # Nejdřív zjistíme, kdo dojel
        finished_cars = [v for v in self.vehicles if v.position >= self.length]
        self.stats_cars_finished += len(finished_cars)
        
        # Ponecháme jen auta, co jsou stále na silnici
        self.vehicles = [v for v in self.vehicles if v.position < self.length]
        
        # Výpočet průměrné rychlosti (pro statistiky)
        if len(self.vehicles) > 0:
            total_speed = sum(v.speed for v in self.vehicles)
            self.stats_avg_speed = (total_speed / len(self.vehicles)) * 3.6 # Převod na km/h
        else:
            self.stats_avg_speed = 0.0


# --- Mozek křižovatky ---
class IntersectionController:
    """
    Řídí dva semafory na křížení cest. Zajišťuje, že nemohou mít oba zelenou.
    """
    def __init__(self, light_h, light_v, green_duration=5.0, red_clearance=2.0):
        self.light_h = light_h
        self.light_v = light_v
        
        # Nastavení časů
        self.green_duration = green_duration  # Jak dlouho svítí zelená
        self.red_clearance = red_clearance    # Jak dlouho je "ticho" mezi přepnutím
        
        self.timer = 0.0
        self.state = "H_GREEN" # Počáteční stav
        
        # Aplikace počátečního stavu
        self.light_h.is_green = True
        self.light_v.is_green = False

    def update(self, dt):
        self.timer += dt
        
        # --- Logika Stavového Automatu ---
        
        # 1. Stav: Horizontální má zelenou
        if self.state == "H_GREEN":
            if self.timer >= self.green_duration:
                # Čas vypršel -> Vypneme H, zapneme VŠECHNY ČERVENÉ
                self.change_state("TO_VERTICAL") # Přejdeme do mezistavu

        # 2. Stav: Všichni červená (přechod na vertikální)
        elif self.state == "TO_VERTICAL":
            if self.timer >= self.red_clearance:
                # Bezpečná pauza vypršela -> Zapneme V
                self.change_state("V_GREEN")

        # 3. Stav: Vertikální má zelenou
        elif self.state == "V_GREEN":
            if self.timer >= self.green_duration:
                # Čas vypršel -> Vypneme V, zapneme VŠECHNY ČERVENÉ
                self.change_state("TO_HORIZONTAL")

        # 4. Stav: Všichni červená (přechod na horizontální)
        elif self.state == "TO_HORIZONTAL":
            if self.timer >= self.red_clearance:
                # Bezpečná pauza vypršela -> Zapneme H
                self.change_state("H_GREEN")

    def change_state(self, new_state):
        """Pomocná metoda pro změnu stavu a reset časovače."""
        self.state = new_state
        self.timer = 0.0
        
        # Nastavení světel podle nového stavu
        if new_state == "H_GREEN":
            self.light_h.is_green = True
            self.light_v.is_green = False
            print("Křižovatka: HORIZONTÁLNÍ ZELENÁ")
            
        elif new_state == "V_GREEN":
            self.light_h.is_green = False
            self.light_v.is_green = True
            print("Křižovatka: VERTIKÁLNÍ ZELENÁ")
            
        else:
            # Stavy TO_VERTICAL a TO_HORIZONTAL znamenají celo-červenou
            self.light_h.is_green = False
            self.light_v.is_green = False
            print("Křižovatka: BEZPEČNOSTNÍ PAUZA (Vše červená)")


# --- 5. GENERÁTOR DOPRAVY ---

class TrafficGenerator:
    """
    Třída, která se stará o automatické generování dopravy.
    """
    def __init__(self, roads):
        self.roads = roads # Seznam silnic [road_h, road_v]
        # Každá silnice bude mít svůj časovač
        self.timers = {road: 0.0 for road in roads}
        self.next_spawns = {road: 0.0 for road in roads}

    def update(self, dt):
        for road in self.roads:
            self.timers[road] += dt
            if self.timers[road] >= self.next_spawns[road]:
                if self.spawn_vehicle(road):
                    self.timers[road] = 0.0
                    self.next_spawns[road] = random.uniform(5.0, 10.0)

    def spawn_vehicle(self, road):
        """Vytvoří náhodné vozidlo a přidá ho na silnici, pokud je volno."""
        
        # 1. Kontrola místa
        road.vehicles.sort(key=lambda v: v.position)
        if len(road.vehicles) > 0:
            if road.vehicles[0].position < 40.0:
                return False 

        # 2. Výběr typu
        vehicle_type = random.choices([Car, Truck, Bus], weights=[50, 20, 30], k=1)[0]
        
        # 3. Rychlost
        speed = random.uniform(20, 30)

        # 4. Vytvoření
        new_vehicle = vehicle_type(position=-10.0, speed=speed)
        road.add_vehicle(new_vehicle)
        
        # Pro debug vypíšeme info
        print(f"Generátor: Přidáno {vehicle_type.__name__} (Rychlost: {speed:.1f} m/s)")
        return True


# --- 6. VIZUALIZACE (Pygame) ---

class Visualizer:
    def __init__(self, roads, generator=None, width=1000, height=700):
        self.roads = roads # Seznam silnic
        self.generator = generator
        self.width = width
        self.height = height
        self.scale = 1.0 
        
        pygame.init()
        self.screen = pygame.display.set_mode((self.width, self.height))
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont("Arial", 16)

    def draw_road_surface(self, road):
        # Kreslení šedého pruhu silnice
        if road.direction == 'H':
            # Vodorovná
            pygame.draw.rect(self.screen, (50, 50, 50), 
                             (road.start_x, road.start_y - 20, road.length, 40))
            pygame.draw.line(self.screen, (255, 255, 255), 
                             (road.start_x, road.start_y), (road.start_x + road.length, road.start_y), 2)
        else:
            # Svislá
            pygame.draw.rect(self.screen, (50, 50, 50), 
                             (road.start_x - 20, road.start_y, 40, road.length))
            pygame.draw.line(self.screen, (255, 255, 255), 
                             (road.start_x, road.start_y), (road.start_x, road.start_y + road.length), 2)

    def draw_vehicle(self, v, road):
        length = v.get_length() * self.scale
        width = 10 # Grafická šířka
        
        # Výpočet souřadnic
        if road.direction == 'H':
            # Vodorovně: x se mění, y je fixní
            x = road.start_x + (v.position * self.scale) - length
            y = road.start_y + 6
            rect = (x, y, length, width)
        else:
            # Svisle: x je fixní, y se mění
            # Pozor: Auto jede dolů, takže délku odečítáme od Y
            x = road.start_x - 15
            y = road.start_y + (v.position * self.scale) - length
            # Pro svislé auto prohodíme šířku a délku
            rect = (x, y, width, length)
            
        # Barva
        color = v.color
        if v.stopped:
             color = (max(0, v.color[0]-50), max(0, v.color[1]-50), max(0, v.color[2]-50))

        pygame.draw.rect(self.screen, color, rect)

    def draw_lights(self, road):
        for light in road.traffic_lights:
            if road.direction == 'H':
                x = road.start_x + light.position
                y = road.start_y + 30
            else:
                x = road.start_x - 30
                y = road.start_y + light.position
                
            color = (0, 255, 0) if light.is_green else (255, 0, 0)
            pygame.draw.circle(self.screen, color, (int(x), int(y)), 8)

    def draw_ui(self):
        """Vykreslí informační panel se statistikami."""
        # 1. Podkladový panel (poloprůhledný)
        ui_surface = pygame.Surface((240, 110)) 
        ui_surface.set_alpha(200) 
        ui_surface.fill((0, 0, 0)) 
        self.screen.blit(ui_surface, (10, 10))
        
        # 2. Výpočet souhrnných statistik ze všech silnic
        total_cars = sum(len(r.vehicles) for r in self.roads)
        total_finished = sum(r.stats_cars_finished for r in self.roads)
        
        # Výpočet globální průměrné rychlosti
        all_speeds = []
        for r in self.roads:
            for v in r.vehicles:
                all_speeds.append(v.speed)
        
        if len(all_speeds) > 0:
            avg_speed = (sum(all_speeds) / len(all_speeds)) * 3.6 # Převod m/s -> km/h
        else:
            avg_speed = 0.0

        # 3. Vykreslení textů
        text_count = self.font.render(f"Aut na scéně: {total_cars}", True, (255, 255, 255))
        self.screen.blit(text_count, (20, 20))
        
        text_finished = self.font.render(f"Dojelo do cíle: {total_finished}", True, (0, 255, 0))
        self.screen.blit(text_finished, (20, 45))
        
        # Barva rychlosti (Zelená > 50, Oranžová > 20, Červená pomalu)
        color_speed = (0, 255, 0) if avg_speed > 50 else (255, 100, 0) if avg_speed > 20 else (255, 0, 0)
        text_speed = self.font.render(f"Prům. rychlost: {avg_speed:.1f} km/h", True, color_speed)
        self.screen.blit(text_speed, (20, 70))
        
        # Info o stavu semaforu
        if hasattr(self, 'intersection_ctrl'):
            state_text = self.font.render(f"Fáze: {self.intersection_ctrl.state}", True, (200, 200, 200))
            self.screen.blit(state_text, (20, 95))

    def run(self):
        running = True
        dt = 0.016
        
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT: running = False

            # --- 1. UPDATE LOGIKY (Výpočty) ---
            if self.generator: self.generator.update(dt)
            
            for road in self.roads:
                road.update(dt)
            
            if hasattr(self, 'intersection_ctrl'):
                self.intersection_ctrl.update(dt)

            # --- 2. VYKRESLOVÁNÍ (Grafika) ---
            self.screen.fill((30, 30, 30))
            
            # VRSTVA 1: Silnice (Podklad)
            # Nejdřív nakreslíme asfalt všech silnic, aby tvořily souvislý povrch
            for road in self.roads:
                self.draw_road_surface(road)

            # VRSTVA 2: ZÁPLATA KŘIŽOVATKY (Novinka)
            # Najdeme souřadnice křižovatky
            cross_x = 0
            cross_y = 0
            # Předpokládáme, že máme jednu V a jednu H silnici
            for r in self.roads:
                if r.direction == 'V': cross_x = r.start_x
                if r.direction == 'H': cross_y = r.start_y
            
            # Nakreslíme čtverec přesně uprostřed, barva stejná jako asfalt (50, 50, 50)
            pygame.draw.rect(self.screen, (50, 50, 50), (cross_x - 20, cross_y - 20, 40, 40))
            
            # VRSTVA 3: Semafory (Pod auty nebo nad auty? Spíše pod, aby do nich auta nenarážela vizuálně)
            # Ale v 2D top-down je lepší mít světla viditelná vždy.
            for road in self.roads:
                self.draw_lights(road)

            # VRSTVA 4: Vozidla (Musí být VŽDY nahoře na asfaltu)
            for road in self.roads:
                for v in road.vehicles:
                    self.draw_vehicle(v, road)

            # VRSTVA 5: UI (Úplně nahoře)
            self.draw_ui()
            
            pygame.display.flip()
            self.clock.tick(60)


# --- SPUŠTĚNÍ ---

if __name__ == "__main__":
    # --- Nastavení světa ---
    
    # 1. Vodorovná silnice (Jede zleva doprava, uprostřed obrazovky)
    road_h = Road(length=1000, direction='H', start_x=0, start_y=350)
    
    # 2. Svislá silnice (Jede shora dolů, kříží vodorovnou na metru 500)
    # Startuje na X=500, Y=0
    road_v = Road(length=700, direction='V', start_x=500, start_y=0)
    
    # --- Semafory ---
    # Křižovatka je na pozici 500m (horizontálně) a 350m (vertikálně)
    light_h = TrafficLight(position=500 - 30) # Zastavíme kousek před středem
    light_v = TrafficLight(position=350 - 30) # Zastavíme kousek před středem
    
    # Přidáme semafory na silnice (POZOR: Musí být typu TrafficLight, ne Smart/Cyclic, 
    # protože je bude řídit náš nový IntersectionController)
    road_h.add_traffic_light(light_h)
    road_v.add_traffic_light(light_v)
    
    # --- Řadič křižovatky ---
    # 8 sekund zelená, 2 sekundy všichni stojí
    crossroad_controller = IntersectionController(light_h, light_v, green_duration=8.0, red_clearance=2.0)
    
    roads = [road_h, road_v]
    generator = TrafficGenerator(roads)
    app = Visualizer(roads, generator=generator)
    
    # Předáme řadič
    app.intersection_ctrl = crossroad_controller
    
    app.run()