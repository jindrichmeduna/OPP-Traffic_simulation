import random
import pygame

# --- KONSTANTY SMĚRŮ ---
DIR_RIGHT = "RIGHT" # Doprava
DIR_LEFT  = "LEFT"  # Doleva
DIR_DOWN  = "DOWN"  # Dolů
DIR_UP    = "UP"    # Nahoru

# --- 1. RODIČOVSKÉ TŘÍDY (Dědičnost) ---
class Vehicle:
    """
    Základní třída pro všechna vozidla.
    Ostatní auta (Car, Truck, Bus) z ní budou dědit.
    """
    def __init__(self, position, speed, acceleration, direction):
        self.position = position  # Pozice v metrech
        self.speed = speed        # Rychlost v m/s
        self.max_speed = speed    # Maximální rychlost pro opětovné rozjetí
        self.acceleration = acceleration
        self.direction = direction  # Směr jízdy

        # Jak dlouho řidič "kouká", než se rozjede (1.1 vteřiny)
        self.start_delay = 1.1
        # Odpočet času
        self.current_wait = 0.0

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
    def __init__(self, speed, position, direction):
        super().__init__(position, speed, acceleration = 7.0, direction = direction)
        self.color = (0, 100, 255) # Modrá

    def get_length(self):
        return 10  # Osobák je nejkratší


class Bus(Vehicle):
    def __init__(self, speed, position, direction):
        super().__init__(position, speed, acceleration = 5, direction = direction)
        self.color = (255, 255, 0) # Žlutá

    def get_length(self):
        return 20 # Autobus je střední délky


class Truck(Vehicle):
    def __init__(self, speed, position, direction):
        super().__init__(position, speed, acceleration = 3, direction = direction)
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
    def __init__(self, length, direction = 'H', start_x=0, start_y=0, reverse=False):
        self.length = length
        self.direction = direction # 'H' = Horizontal, 'V' = Vertical
        self.reverse = reverse     # Reverzní směr (doleva / nahoru)
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
            should_stop = False
            
            # --- A) Resetování stavu a Akcelerace ---
            if not vehicle.stopped:
                # Pokud auto jede pomaleji než je jeho maximálka, zrychlujeme
                if vehicle.speed < vehicle.max_speed:
                    # Vzorec: rychlost = rychlost + zrychlení * čas
                    vehicle.speed += vehicle.acceleration * dt
                    
                    # Pojistka: nesmíme překročit maximálku
                    if vehicle.speed > vehicle.max_speed:
                        vehicle.speed = vehicle.max_speed

            # --- B) Reakce na semafory ---
            for light in self.traffic_lights:
                distance = light.position - vehicle.position
                if 10 < distance < 100:
                    # Přibližujeme se k semaforu - můžeme začít brzdit
                    if not light.is_green:
                        # Vypočítáme potřebné zpomalení, abychom zastavili před semaforem
                        time_to_brake = distance / max(vehicle.speed, 0.1) # Vyhneme se dělení nulou
                        required_deceleration = vehicle.speed / time_to_brake
                        
                        # Aplikujeme zpomalení (brzdíme)
                        vehicle.speed -= required_deceleration * dt
                        
                # Pokud je semafor blízko (méně než 10m) a je červená
                if 0 < distance < 10 and not light.is_green:
                    should_stop = True # Důvod k zastavení 1: Červená
                    break

            # --- C) Reakce na vozidla (Adaptivní tempomat) ---
            # Podíváme se, jestli je před námi nějaké auto
            # i + 1 je index auta před námi (protože jsme je seřadili)
            if i < len(self.vehicles) - 1:
                vehicle_ahead = self.vehicles[i+1]
                
                # Vypočítáme mezeru (od čumáku našeho auta k zadku auta před námi)
                # vehicle_ahead.get_length() je důležité, abychom do něj nevjeli polovinou
                gap = vehicle_ahead.position - vehicle.position - vehicle_ahead.get_length()
                
                # Dynamická bezpečná vzdálenost (čím rychleji jedu, tím větší mezeru chci)
                # Pravidlo 2 sekund: safe_dist = rychlost * 1.5 + rezerva
                safe_distance = (vehicle.speed * 1.5) + 5.0
                
                if gap < safe_distance:
                    # HROZÍ SRÁŽKA!
                    
                    if vehicle_ahead.stopped or vehicle_ahead.speed == 0:
                        # Pokud auto před námi stojí a jsme fakt blízko -> Zastavíme taky
                        if gap < 5.0: # 5 metrů od nárazníku
                            should_stop = True # Důvod k zastavení 2: Auto před námi stojí
                        else:
                            # Brzdíme
                            time_to_brake = gap / max(vehicle.speed, 0.1) # Vyhneme se dělení nulou
                            required_deceleration = vehicle.speed / time_to_brake
                        
                            # Aplikujeme zpomalení (brzdíme)
                            vehicle.speed -= required_deceleration * dt
                    else:
                        # Auto před námi jede, ale pomaleji -> přizpůsobíme rychlost
                        vehicle.speed = min(vehicle_ahead.speed - 2, vehicle.max_speed)

            # --- D) FINÁLNÍ ROZHODNUTÍ ---
            # Rozhodujeme až teď, když známe oba důvody (semafor i zácpu)
            if should_stop:
                vehicle.stop()
                # Jakmile zastavíme, nastavíme "budík" na příští rozjezd.
                # Auto bude muset čekat, až uběhne jeho start_delay.
                vehicle.current_wait = vehicle.start_delay
            
            elif vehicle.stopped:
                # ZMĚNA: Auto by mohlo jet (should_stop je False), ALE...
                # ...musí uběhnout reakční doba řidiče!
                
                vehicle.current_wait -= dt # Odpočítáváme čas
                
                # Teprve až čas vyprší (je menší nebo roven nule), skutečně odbrzdíme
                if vehicle.current_wait <= 0:
                    vehicle.stopped = False

            # 3. Aplikace pohybu
            if vehicle.speed < 0:
                vehicle.stop()
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
    def __init__(self, lights_h, lights_v, green_duration=8.0, red_clearance=2.0):
        self.lights_h = lights_h # Očekáváme seznam (list)
        self.lights_v = lights_v # Očekáváme seznam (list)
        self.green_duration = green_duration
        self.red_clearance = red_clearance
        self.timer = 0.0
        self.state = "H_GREEN"
        
        # Nastavení startovního stavu
        self.set_lights(self.lights_h, True)
        self.set_lights(self.lights_v, False)

    def set_lights(self, lights, is_green):
        """Pomocná metoda, která přepne všechny semafory v seznamu."""
        for l in lights:
            l.is_green = is_green

    def update(self, dt):
        self.timer += dt
        if self.state == "H_GREEN":
            if self.timer >= self.green_duration: self.change_state("TO_VERTICAL")
        elif self.state == "TO_VERTICAL":
            if self.timer >= self.red_clearance: self.change_state("V_GREEN")
        elif self.state == "V_GREEN":
            if self.timer >= self.green_duration: self.change_state("TO_HORIZONTAL")
        elif self.state == "TO_HORIZONTAL":
            if self.timer >= self.red_clearance: self.change_state("H_GREEN")

    def change_state(self, new_state):
        self.state = new_state
        self.timer = 0.0
        if new_state == "H_GREEN":
            self.set_lights(self.lights_h, True)
            self.set_lights(self.lights_v, False)
        elif new_state == "V_GREEN":
            self.set_lights(self.lights_h, False)
            self.set_lights(self.lights_v, True)
        else:
            self.set_lights(self.lights_h, False)
            self.set_lights(self.lights_v, False)


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
            
        # 2. Určení směru podle silnice
        direction = DIR_RIGHT # Default
        if road.direction == 'H':
            # Pokud je silnice reverzní, jede doleva, jinak doprava
            direction = DIR_LEFT if road.reverse else DIR_RIGHT
        else:
            # Pokud je silnice reverzní, jede nahoru, jinak dolů
            direction = DIR_UP if road.reverse else DIR_DOWN

        # 3. Výběr typu
        vehicle_type = random.choices([Car, Truck, Bus], weights=[50, 20, 30], k=1)[0]
        
        # 4. Rychlost
        if vehicle_type == Car:
            speed = random.uniform(23, 27)
        elif vehicle_type == Bus:
            speed = random.uniform(18, 22)
        elif vehicle_type == Truck:
            speed = random.uniform(13, 17)

        # 5. Vytvoření
        new_vehicle = vehicle_type(position=-10.0, speed=speed, direction=direction)
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
        width = 10 
        lane_offset = 10 # Vzdálenost středu pruhu od středu silnice
        
        # Souřadnice levého horního rohu pro vykreslení
        x, y = 0, 0
        rect_width, rect_height = 0, 0

        # --- LOGIKA PODLE SMĚRU VOZIDLA ---
        
        if v.direction == DIR_RIGHT:
            # Jede doprava -> dolní pruh (+ offset)
            # Position se přičítá k X
            x = road.start_x + (v.position * self.scale) - length
            y = road.start_y + lane_offset - (width // 2) + 1
            rect_width, rect_height = length, width

        elif v.direction == DIR_LEFT:
            # Jede doleva -> horní pruh (- offset)
            # Position se ODČÍTÁ od konce silnice (protože position je ujetá vzdálenost)
            # Start silnice (vizuálně) je vpravo: road.start_x + road.length
            x = (road.start_x + road.length) - (v.position * self.scale)
            y = road.start_y - lane_offset - (width // 2)
            rect_width, rect_height = length, width

        elif v.direction == DIR_DOWN:
            # Jede dolů -> pravý pruh (- offset)
            # Position se přičítá k Y
            x = road.start_x - lane_offset - (width // 2)
            y = road.start_y + (v.position * self.scale) - length
            rect_width, rect_height = width, length # Prohozené rozměry

        elif v.direction == DIR_UP:
            # Jede nahoru -> levý pruh (+ offset)
            # Position se ODČÍTÁ od konce silnice (dole)
            x = road.start_x + lane_offset - (width // 2) + 1
            y = (road.start_y + road.length) - (v.position * self.scale)
            rect_width, rect_height = width, length # Prohozené rozměry
            
        # Barva
        color = v.color
        if v.stopped:
             color = (max(0, v.color[0]-50), max(0, v.color[1]-50), max(0, v.color[2]-50))

        pygame.draw.rect(self.screen, color, (x, y, rect_width, rect_height))

    def draw_lights(self, road):
        for light in road.traffic_lights:
            if road.direction == 'H':
                if road.reverse:
                    x = road.start_x + road.length - light.position
                    y = road.start_y - 30
                else:
                    x = road.start_x + light.position
                    y = road.start_y + 30
            else:
                if road.reverse:
                    x = road.start_x + 30
                    y = road.start_y + road.length - light.position
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

    # Střed křižovatky
    CX, CY = 500, 350
    
    # 1. Definice 4 silnic (každá má 2 pruhy, jeden reverse)
    road_h_right = Road(1000, 'H', 0, CY, reverse=False)
    road_h_left  = Road(1000, 'H', 0, CY, reverse=True)
    road_v_down  = Road(700, 'V', CX, 0, reverse=False)
    road_v_up    = Road(700, 'V', CX, 0, reverse=True)
    
    # 2. Definice semaforů
    # Pozice je relativní k začátku jízdy daného pruhu
    l1 = TrafficLight(470) # Pro H Right
    l2 = TrafficLight(470) # Pro H Left
    l3 = TrafficLight(320) # Pro V Down
    l4 = TrafficLight(320) # Pro V Up
    
    # 3. Přiřazení semaforů ke SPRÁVNÝM silnicím
    road_h_right.add_traffic_light(l1)
    road_h_left.add_traffic_light(l2)
    road_v_down.add_traffic_light(l3)
    road_v_up.add_traffic_light(l4)
    
    # 4. Řadič (Bere seznamy semaforů)
    controller = IntersectionController([l1, l2], [l3, l4], 8.0, 2.0)
    
    # 5. Spuštění
    roads = [road_h_right, road_h_left, road_v_down, road_v_up]
    generator = TrafficGenerator(roads)
    
    app = Visualizer(roads, generator, 1000, 700)
    app.intersection_ctrl = controller
    
    app.run()