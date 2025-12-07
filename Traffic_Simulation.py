import random
import pygame

# --- KONSTANTY SMĚRŮ ---
DIR_RIGHT = "RIGHT" # Doprava
DIR_LEFT  = "LEFT"  # Doleva
DIR_DOWN  = "DOWN"  # Dolů
DIR_UP    = "UP"    # Nahoru

# --- 1. RODIČOVSKÉ TŘÍDY (Dědičnost) ---
class Vehicle:
    # Základní třída pro všechna vozidla.
    # Ostatní auta (Car, Truck, Bus) z ní budou dědit.
    def __init__(self, position, speed, acceleration, direction):
        self.position = position         # Pozice v metrech
        self.speed = speed               # Rychlost v m/s
        self.max_speed = speed           # Maximální rychlost pro opětovné rozjetí
        self.acceleration = acceleration # Zrychlení v m/s²
        self.direction = direction       # Směr jízdy
        self.is_braking = False          # Zda auto právě zpomaluje (svítí brzdová světla)
        self.start_delay = 1.1           # Jak dlouho řidič "kouká", než se rozjede (1.1 vteřiny)
        self.current_wait = 0.0          # Odpočet času
        self.stopped = False             # Zda auto stojí
        self.color = "red"               # Jen pro vizualizaci

    def get_length(self):
        # Tuto metodu přepíšeme v potomcích (Car, Truck...).
        return 0.0

    def move(self, dt):
        # Fyzika pohybu. Pokud auto nestojí, posuneme ho.
        if not self.stopped:
            # Dráha = rychlost * čas
            self.position += self.speed * dt

    def stop(self):
        self.stopped = True
        self.speed = 0

    def accelerate(self, acceleration, dt):
        # Zrychlení vozidla
        self.speed += acceleration * dt
        # Pojistka proti překročení maximální rychlosti
        if self.speed > self.max_speed:
            self.speed = self.max_speed

    def brake(self, deceleration, dt):
        # Zpomalení vozidla
        self.is_braking = True
        self.speed -= deceleration * dt
        # Pojistka proti záporné rychlosti
        if self.speed < 0:
            self.speed = 0

    def get_distance_to(self, vehicle_ahead):
        # Vrátí vzdálenost (gap) mezi předním nárazníkem tohoto auta a zadním nárazníkem auta před ním.
        if vehicle_ahead is None:
            return 99999.0 # Nekonečno (žádné auto před námi)
            
        # Vzorec: Pozice auta vpředu - Moje pozice - Délka auta vpředu
        return vehicle_ahead.position - self.position - vehicle_ahead.get_length()        


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


class Train(Vehicle):
    def __init__(self, speed, position, direction):
        super().__init__(position, speed, acceleration=0.0, direction=direction)
        self.color = (200, 200, 200) # Šedý/Stříbrný
        self.stopped = False # Pojistka

    def get_length(self):
        return 120.0 

    def stop(self):
        # Přepsání metody (Polymorfismus): Vlak NIKDY nezastaví
        pass


# --- 3. SEMAFORY (Polymorfismus) ---

class TrafficLight:
    # Základní třída pro semafor (Rozhraní).
    def __init__(self, position):
        self.position = position
        self.is_green = True

    def update(self, dt, vehicles):
        # Metoda update přijímá i seznam vozidel, aby 'chytré' semafory mohly reagovat na provoz.
        pass


class CyclicTrafficLight(TrafficLight):
    # Klasický semafor - přepíná časově, auta ignoruje.
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
    # Inteligentní semafor. Defaultně je červená. Zelenou pustí jen, když se blíží auto.
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
    def __init__(self, length, direction = 'H', start_x=0, start_y=0, reverse=False, road_type="road"):
        self.length = length
        self.direction = direction      # 'H' = Horizontal, 'V' = Vertical
        self.reverse = reverse          # Reverzní směr (doleva / nahoru)
        self.start_x = start_x
        self.start_y = start_y
        self.vehicles = []              # Seznam vozidel
        self.traffic_lights = []        # Seznam semaforů
        self.road_type = road_type      # "road" nebo "rail" (pro vlaky)
        self.stats_cars_finished = 0    # Počet aut, co dojela do cíle
        self.stats_avg_speed = 0.0      # Průměrná rychlost aut na silnici

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

            # Vzdálenost od vozidla před námi
            if i < len(self.vehicles) - 1:
                vehicle_ahead_exists = True
                vehicle_ahead = self.vehicles[i+1]
                gap = vehicle.get_distance_to(vehicle_ahead)
            else:
                vehicle_ahead_exists = False
            
            # --- A) Resetování stavu a Akcelerace ---
            if not vehicle.stopped:
                vehicle.is_braking = False
                # Pokud auto jede pomaleji než je jeho maximálka, zrychlujeme
                if vehicle.speed < vehicle.max_speed:
                    vehicle.accelerate(vehicle.acceleration, dt)

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
                        vehicle.brake(required_deceleration, dt)
                        
                # Pokud je semafor blízko (méně než 10m) a je červená
                if 0 < distance < 10:
                    # a) Červená -> STŮJ
                    if not light.is_green:
                        should_stop = True
                    
                    # b) Zelená -> KONTROLA MÍSTA ZA KŘIŽOVATKOU (Anti-Gridlock)
                    else:
                        # Podíváme se na auto před námi
                        if vehicle_ahead_exists:
                            # Odhad šířky křižovatky + rezerva
                            intersection_width = 60 + vehicle.get_length() # Základní šířka + délka našeho auta
                            if gap < intersection_width and (vehicle_ahead.speed < 10.0 or (vehicle.speed > vehicle_ahead.speed and (vehicle_ahead.max_speed / vehicle_ahead.speed > 1.5 and vehicle_ahead.is_braking))):
                                should_stop = True # I když je zelená, nemůžeme vjet!

            # --- C) Reakce na vozidla (Adaptivní tempomat) ---
            # Podíváme se, jestli je před námi nějaké auto
            # i + 1 je index auta před námi (protože jsme je seřadili)
            if vehicle_ahead_exists:                
                # Dynamická bezpečná vzdálenost (čím rychleji jedu, tím větší mezeru chci)
                safe_distance = (vehicle.speed * 2) + 5.0
                
                if gap < safe_distance:
                    # HROZÍ SRÁŽKA!
                    vehicle.is_braking = True
                    
                    if vehicle_ahead.stopped or vehicle_ahead.speed == 0:
                        # Pokud auto před námi stojí a jsme fakt blízko -> Zastavíme taky
                        if gap < 5.0: # 5 metrů od nárazníku
                            should_stop = True # Důvod k zastavení: Auto před námi stojí
                        else:
                            # Brzdíme
                            time_to_brake = gap / max(vehicle.speed, 0.1) # Vyhneme se dělení nulou
                            required_deceleration = vehicle.speed / time_to_brake
                            # Aplikujeme zpomalení (brzdíme)
                            vehicle.brake(required_deceleration, dt)
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
                # Auto by mohlo jet (should_stop je False), ALE musí uběhnout reakční doba řidiče!
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
        finished_cars = [v for v in self.vehicles if (v.position - v.get_length()) >= self.length]
        self.stats_cars_finished += len(finished_cars)
        
        # Ponecháme jen auta, co jsou stále na silnici
        self.vehicles = [v for v in self.vehicles if (v.position - v.get_length()) < self.length]
        
        # Výpočet průměrné rychlosti (pro statistiky)
        if len(self.vehicles) > 0:
            total_speed = sum(v.speed for v in self.vehicles)
            self.stats_avg_speed = (total_speed / len(self.vehicles)) * 3.6 # Převod na km/h
        else:
            self.stats_avg_speed = 0.0


# --- Mozek křižovatky ---
class IntersectionController:
    # Řídí dva semafory na křížení cest. Zajišťuje, že nemohou mít oba zelenou.
    def __init__(self, lights_h, lights_v, green_duration=10.0, red_clearance=2.0):
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
        # Pomocná metoda, která přepne všechny semafory v seznamu.
        for l in lights:
            l.is_green = is_green

    def update(self, dt):
        self.timer += dt
        if self.state == "H_GREEN":
            if self.timer >= self.green_duration:
                self.change_state("TO_VERTICAL")
        elif self.state == "TO_VERTICAL":
            if self.timer >= self.red_clearance:
                self.change_state("V_GREEN")
        elif self.state == "V_GREEN":
            if self.timer >= self.green_duration:
                self.change_state("TO_HORIZONTAL")
        elif self.state == "TO_HORIZONTAL":
            if self.timer >= self.red_clearance:
                self.change_state("H_GREEN")

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


class SmartIntersectionController:
    # Chytrý řadič, který se rozhoduje podle délky front v jednotlivých směrech.
    def __init__(self, roads_h, roads_v, lights_h, lights_v, min_green_time=5.0, max_green_time=20.0, red_clearance=2.0):
        self.roads_h = roads_h     # Seznam horizontálních silnic
        self.roads_v = roads_v     # Seznam vertikálních silnic
        self.lights_h = lights_h   # Seznam semaforů H
        self.lights_v = lights_v   # Seznam semaforů V
        
        # Nastavení limitů
        self.min_green_time = min_green_time # Minimální doba zelené (proti blikání)
        self.max_green_time = max_green_time # Maximální doba (aby se dostalo na každého)
        self.red_clearance = red_clearance   # Vyklízecí čas
        
        self.timer = 0.0
        self.state = "H_GREEN" # Začínáme zelenou pro H
        
        # Start
        self.set_lights(self.lights_h, True)
        self.set_lights(self.lights_v, False)

    def set_lights(self, lights, is_green):
        for l in lights:
            l.is_green = is_green

    def count_queue(self, roads):
        # Spočítá, kolik aut čeká (nebo se blíží) ke křižovatce na daných silnicích.
        count = 0
        for road in roads:
            # Hledáme semafor na této silnici
            if not road.traffic_lights:
                continue
            
            # Kde je semafor?
            light_pos = road.traffic_lights[0].position
            
            # Počítáme auta, která jsou v zóně 0 až 100m před semaforem
            for v in road.vehicles:
                dist = light_pos - v.position
                if 0 < dist < 100:
                    count += 1
        return count

    def update(self, dt):
        self.timer += dt
        
        # --- LOGIKA STAVOVÉHO AUTOMATU ---
        # Spočítáme fronty
        queue_h = self.count_queue(self.roads_h) # Počet aut na horizontálních silnicích
        queue_v = self.count_queue(self.roads_v) # Počet aut na vertikálních silnicích
        
        if self.state == "H_GREEN":
            # 1. Musíme dodržet minimální čas
            if self.timer < self.min_green_time:
                return

            # 2. Pokud jsme překročili maximální čas, musíme přepnout
            if self.timer > self.max_green_time:
                self.change_state("TO_VERTICAL")
                return

            # 3. CHYTRÉ ROZHODOVÁNÍ          
            # Pokud na červené čeká více aut než kolik jede na zelené, přepni.
            # Přidáme malý práh (+2), abychom nepřepínali zbytečně při rovnosti.
            if queue_v > queue_h + 2:
                print(f"SMART: Přepínám na V (Fronta V:{queue_v} vs H:{queue_h})")
                self.change_state("TO_VERTICAL")

        elif self.state == "TO_VERTICAL":
            if self.timer >= self.red_clearance:
                self.change_state("V_GREEN")

        elif self.state == "V_GREEN":
            # To samé zrcadlově pro Vertikální směr
            if self.timer < self.min_green_time: return
            if self.timer > self.max_green_time:
                self.change_state("TO_HORIZONTAL")
                return
            
            if queue_h > queue_v + 2:
                print(f"SMART: Přepínám na H (Fronta H:{queue_h} vs V:{queue_v})")
                self.change_state("TO_HORIZONTAL")

        elif self.state == "TO_HORIZONTAL":
            if self.timer >= self.red_clearance:
                self.change_state("H_GREEN")

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
            # Vyklízecí fáze (všichni červená)
            self.set_lights(self.lights_h, False)
            self.set_lights(self.lights_v, False)


class RailwayController:
    # Řídí železniční přejezd. Auta mají zelenou, dokud se neobjeví vlak.
    def __init__(self, tracks, crossing_lights, crossing_point):
        self.tracks = tracks           # Seznam kolejí
        self.crossing_lights = crossing_lights # Semafory na silnici před přejezdem
        self.crossing_point = crossing_point # Pozice přejezdu na silnici (v metrech)
        self.state = "OPEN"            # OPEN (auta jedou) / CLOSED (vlak jede)
        self.safety_timer = 0.0
        
        # Defaultně zelená pro auta
        self.set_lights(True)

    def set_lights(self, is_green):
        for l in self.crossing_lights:
            l.is_green = is_green

    def update(self, dt):
        # 1. Detekce vlaku
        train_approaching = False
         
        for track in self.tracks:
            # Pokud kolej vede "pozpátku" (reverse), musíme souřadnici otočit.
            if track.reverse:
                current_crossing_pos = track.length - self.crossing_point
            else:
                current_crossing_pos = self.crossing_point

            # Detekční zóna se počítá pro každou kolej zvlášť
            detection_zone_start = current_crossing_pos - 250 
            detection_zone_end   = current_crossing_pos + 200 
            
            for v in track.vehicles:
                if detection_zone_start < v.position < detection_zone_end:
                    train_approaching = True

        # 2. Stavový automat
        if self.state == "OPEN":
            if train_approaching:
                print("PŘEJEZD: Pozor, vlak! Červená.")
                self.state = "CLOSED"
                self.set_lights(False) # Červená pro auta

        elif self.state == "CLOSED":
            if not train_approaching:
                print("PŘEJEZD: Vlak projel. Zelená.")
                self.state = "OPEN"
                self.set_lights(True) # Zelená pro auta


# --- 5. GENERÁTOR DOPRAVY ---

class TrafficGenerator:
    # Třída, která se stará o automatické generování dopravy.
    def __init__(self, roads):
        self.roads = roads # Seznam silnic
        # Každá silnice bude mít svůj časovač
        self.timers = {road: 0.0 for road in roads}
        self.next_spawns = {road: 0.0 for road in roads}

    def update(self, dt):
        for road in self.roads:
            self.timers[road] += dt
            if self.timers[road] >= self.next_spawns[road]:
                if self.spawn_vehicle(road):
                    self.timers[road] = 0.0

                    if road.road_type == "rail":
                        # Vlaky jezdí zřídka (např. jednou za 45 až 75 sekund)
                        self.next_spawns[road] = random.uniform(45, 75)
                    else:
                        # Auta jezdí často (např. jednou za 3 až 7 sekund)
                        self.next_spawns[road] = random.uniform(3.0, 7.0)

    def spawn_vehicle(self, road):
        # Vytvoří náhodné vozidlo a přidá ho na silnici, pokud je volno.
        
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
        if road.road_type == "rail":
            # Pokud jsou to koleje, VŽDY generujeme vlak
            vehicle_type = Train
            speed = random.uniform(35, 45) # Rychlý vlak

        else:
            # Jinak je to silnice -> generujeme auta
            vehicle_type = random.choices([Car, Truck, Bus], weights=[70, 20, 10], k=1)[0]
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
        if road.reverse: return # Kreslíme podklad jen jednou
        
        if road.road_type == "road":
            # --- VYKRESLENÍ SILNIC ---
            if road.direction == 'H':
                # HORIZONTÁLNÍ SILNICE
                # 1. Silnice
                pygame.draw.rect(self.screen, (50, 50, 50), 
                                (road.start_x, road.start_y - 20, road.length, 40))
                # 2. Středová čára
                pygame.draw.line(self.screen, (255, 255, 255), 
                                (road.start_x, road.start_y), (road.start_x + road.length, road.start_y), 2)
            else:
                # VERTIKÁLNÍ SILNICE
                # 1. Silnice
                pygame.draw.rect(self.screen, (50, 50, 50), 
                                (road.start_x - 20, road.start_y, 40, road.length))
                # 2. Středová čára
                pygame.draw.line(self.screen, (255, 255, 255), 
                                (road.start_x, road.start_y), (road.start_x, road.start_y + road.length), 2)

        else:
            # --- VYKRESLENÍ KOLEJÍ ---
            if road.direction == 'V':
                # VERTIKÁLNÍ KOLEJE
                # 1. Štěrk
                pygame.draw.rect(self.screen, (100, 80, 50), (road.start_x - 16, road.start_y, 33, road.length))
                # 2. Pražce (vodorovné čárky)
                for i in range(0, road.length, 10):
                    y = road.start_y + i
                    pygame.draw.line(self.screen, (60, 40, 20), (road.start_x - 16, y), (road.start_x + 16, y), 4)
                # 3. Kolejnice (svislé čáry)
                pygame.draw.line(self.screen, (180, 180, 180), (road.start_x - 8, road.start_y), (road.start_x - 8, road.start_y + road.length), 2)
                pygame.draw.line(self.screen, (180, 180, 180), (road.start_x + 7, road.start_y), (road.start_x + 7, road.start_y + road.length), 2)
                pygame.draw.line(self.screen, (180, 180, 180), (road.start_x - 14, road.start_y), (road.start_x - 14, road.start_y + road.length), 2)
                pygame.draw.line(self.screen, (180, 180, 180), (road.start_x + 13, road.start_y), (road.start_x + 13, road.start_y + road.length), 2)
            
            else: 
                # HORIZONTÁLNÍ KOLEJE
                # 1. Štěrk
                pygame.draw.rect(self.screen, (100, 80, 50), (road.start_x, road.start_y - 16, road.length, 33))
                # 2. Pražce (svislé čárky)
                for i in range(0, road.length, 10):
                    x = road.start_x + i
                    pygame.draw.line(self.screen, (60, 40, 20), (x, road.start_y - 16), (x, road.start_y + 16), 4)
                # 3. Kolejnice (vodorovné čáry)
                pygame.draw.line(self.screen, (180, 180, 180), (road.start_x, road.start_y - 8), (road.start_x + road.length, road.start_y - 8), 2)
                pygame.draw.line(self.screen, (180, 180, 180), (road.start_x, road.start_y + 7), (road.start_x + road.length, road.start_y + 7), 2)
                pygame.draw.line(self.screen, (180, 180, 180), (road.start_x, road.start_y - 14), (road.start_x + road.length, road.start_y - 14), 2)
                pygame.draw.line(self.screen, (180, 180, 180), (road.start_x, road.start_y + 13), (road.start_x + road.length, road.start_y + 13), 2)
            
    def draw_vehicle(self, v, road):
        # Vykreslí jedno vozidlo na dané silnici.
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
        # Vykreslí semafory na dané silnici.
        for light in road.traffic_lights:
            if road.direction == 'H':
                # Horizontální silnice
                if road.reverse:
                    # Jede doleva
                    x = road.start_x + road.length - light.position
                    y = road.start_y - 30
                else:
                    # Jede doprava
                    x = road.start_x + light.position
                    y = road.start_y + 30
            else:
                # Vertikální silnice
                if road.reverse:
                    # Jede nahoru
                    x = road.start_x + 30
                    y = road.start_y + road.length - light.position
                else:
                    # Jede dolů
                    x = road.start_x - 30
                    y = road.start_y + light.position
                
            color = (0, 255, 0) if light.is_green else (255, 0, 0)
            pygame.draw.circle(self.screen, color, (int(x), int(y)), 8)

    def draw_ui(self):
        # Vykreslí informační panel se statistikami.
        # 1. Podkladový panel (poloprůhledný)
        ui_surface = pygame.Surface((240, 90)) 
        ui_surface.set_alpha(200) 
        ui_surface.fill((0, 0, 0)) 
        ui_x = 10
        ui_y = 180
        self.screen.blit(ui_surface, (ui_x, ui_y))
        
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
        self.screen.blit(text_count, (ui_x + 10, ui_y + 10))
        
        text_finished = self.font.render(f"Dojelo do cíle: {total_finished}", True, (0, 255, 0))
        self.screen.blit(text_finished, (ui_x + 10, ui_y + 35))
        
        # Barva rychlosti (Zelená > 50, Oranžová > 20, Červená pomalu)
        color_speed = (0, 255, 0) if avg_speed > 50 else (255, 100, 0) if avg_speed > 20 else (255, 0, 0)
        text_speed = self.font.render(f"Prům. rychlost: {avg_speed:.1f} km/h", True, color_speed)
        self.screen.blit(text_speed, (ui_x + 10, ui_y + 60))

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
                if road.road_type == "road":
                    self.draw_road_surface(road)

            # VRSTVA 2: ZÁPLATA KŘIŽOVATKY
            # Najdeme souřadnice křižovatky
            # 1. Posbíráme souřadnice všech silnic (ignorujeme koleje)
            vertical_xs = set()
            horizontal_ys = set()
            
            for r in self.roads:
                if r.road_type == "road": # Jen pro silnice (ne koleje)
                    if r.direction == 'V':
                        vertical_xs.add(r.start_x)
                    elif r.direction == 'H':
                        horizontal_ys.add(r.start_y)
            
            # 2. Vykreslíme čtverec na KAŽDÉM průsečíku
            # Projdeme všechny kombinace X a Y
            for cx in vertical_xs:
                for cy in horizontal_ys:
                    # Kreslíme záplatu 40x40 (střed silnic)
                    pygame.draw.rect(self.screen, (50, 50, 50), (cx - 20, cy - 20, 40, 40))
            
            # VRSTVA 3: KOLEJE
            for road in self.roads:
                if road.road_type == "rail":
                    self.draw_road_surface(road)
            
            # VRSTVA 4: SEMAFORY
            for road in self.roads:
                self.draw_lights(road)

            # VRSTVA 5: Vozidla
            for road in self.roads:
                for v in road.vehicles:
                    self.draw_vehicle(v, road)

            # VRSTVA 6: TUNELY (KRYTÍ VLAKŮ)           
            rail_xs = set()
            rail_ys = set()
            for r in self.roads:
                if r.road_type == "rail":
                    if r.direction == 'V': rail_xs.add(r.start_x)
                    elif r.direction == 'H': rail_ys.add(r.start_y)
            
            for rx in rail_xs:
                for ry in rail_ys:
                    # Tunel musí být o kousek větší než koleje (např. 60x60), aby schoval vlak
                    tunnel_size = 60
                    tunnel_rect = (rx - tunnel_size//2, ry - tunnel_size//2, tunnel_size, tunnel_size)
                    
                    # 1. Střecha tunelu (Barva terénu/Beton)
                    pygame.draw.rect(self.screen, (40, 40, 45), tunnel_rect)
                    
                    # 2. Okraj (Rám mostu)
                    pygame.draw.rect(self.screen, (20, 20, 25), tunnel_rect, 4)
                    
                    # 3. Designový prvek (X na střeše nebo šrafování)
                    pygame.draw.line(self.screen, (30, 30, 35), (rx - 20, ry - 20), (rx + 20, ry + 20), 3)
                    pygame.draw.line(self.screen, (30, 30, 35), (rx + 20, ry - 20), (rx - 20, ry + 20), 3)

            # VRSTVA 7: UI (Úplně nahoře)
            self.draw_ui()
            
            pygame.display.flip()
            self.clock.tick(60)


# --- SPUŠTĚNÍ ---

if __name__ == "__main__":
    # --- Nastavení světa ---
    size_width = 1200
    size_height = 700

    # Souřadnice křižovatek a přejezdů
    road1_X = 400
    road1_Y = 350
    road2_X = 400
    road2_Y = 600
    rail1_X = 800
    rail1_Y = 350
    rail2_X = 400
    rail2_Y = 100

    # --- DEFINICE SILNIC A KOLEJÍ  ---
    # 1. Horizontální silnice (Dlouhé 1200m, Křižovatka na x 400 a 800)
    road1_h_right = Road(1200, 'H', 0, road1_Y, reverse=False)
    road1_h_left  = Road(1200, 'H', 0, road1_Y, reverse=True)
    road2_h_right = Road(1200, 'H', 0, road2_Y, reverse=False)
    road2_h_left  = Road(1200, 'H', 0, road2_Y, reverse=True)

    # 2. Vertikální silnice (Dlouhá 700, Křižovatka na y 100 a 600)
    road_v_down = Road(700, 'V', road1_X, 0, reverse=False)
    road_v_up   = Road(700, 'V', road1_X, 0, reverse=True)

    # 3. Horizontální kolej (Dlouhá 1200, Přejezd na x 400)
    rail_h_right = Road(1200, 'H', 0, rail2_Y, reverse=False, road_type="rail")
    rail_h_left  = Road(1200, 'H', 0, rail2_Y, reverse=True, road_type="rail")

    # 4. Vertikální kolej (Dlouhá 700, Přejezd na y 350 a 600)
    rail_v_down = Road(700, 'V', rail1_X, 0, reverse=False, road_type="rail")
    rail_v_up   = Road(700, 'V', rail1_X, 0, reverse=True, road_type="rail")

    # --- SEMAFORY PRO KŘIŽOVATKY A PŘEJEZDY  ---
    # Křižovatka 1 mezi road1_h a road_v (X=400, Y=350)
    l_cross1_h_right = TrafficLight(road1_X - 30)   # Semafor na 370m
    l_cross1_h_left  = TrafficLight(size_width - road1_X - 30)  # Semafor na 770m
    l_cross1_v_down  = TrafficLight(road1_Y - 30)   # Semafor na 320m
    l_cross1_v_up    = TrafficLight(road1_Y - 30)   # Semafor na 320m

    road1_h_right.add_traffic_light(l_cross1_h_right)
    road1_h_left.add_traffic_light(l_cross1_h_left)
    road_v_down.add_traffic_light(l_cross1_v_down)
    road_v_up.add_traffic_light(l_cross1_v_up)

    # Řadič Křižovatky 1 mezi road1_h a road_v (X=400, Y=350)
    smart_intersection_ctrl_1 = SmartIntersectionController(
        [road2_h_right, road2_h_left], 
        [road_v_down, road_v_up],
        [l_cross1_h_right, l_cross1_h_left], 
        [l_cross1_v_down, l_cross1_v_up], 
        min_green_time=5, max_green_time=20.0, red_clearance=2.0
    )

    # Křižovatka 2 mezi road2_h a road_v (X=400, Y=600)
    l_cross2_h_right = TrafficLight(road2_X - 30)   # Semafor na 370m
    l_cross2_h_left  = TrafficLight(size_width - road2_X - 30)  # Semafor na 770m
    l_cross2_v_down  = TrafficLight(road2_Y - 30)   # Semafor na 570m
    l_cross2_v_up    = TrafficLight(size_height - road2_Y - 30) # Semafor na 70m

    road2_h_right.add_traffic_light(l_cross2_h_right)
    road2_h_left.add_traffic_light(l_cross2_h_left)
    road_v_down.add_traffic_light(l_cross2_v_down)
    road_v_up.add_traffic_light(l_cross2_v_up)

    # Řadič Křižovatky 2 mezi road2_h a road_v (X=400, Y=600)
    intersection_ctrl_2 = IntersectionController(
        [l_cross2_h_right, l_cross2_h_left], 
        [l_cross2_v_down, l_cross2_v_up], 
        green_duration=10.0, red_clearance=2.0
    )

    # Přejezd 1 na road1_h (X=800, Y=350)
    l_rail1_h_right = TrafficLight(rail1_X - 30)   # Semafor na 770m
    l_rail1_h_left  = TrafficLight(size_width - rail1_X - 30)  # Semafor na 370m

    road1_h_right.add_traffic_light(l_rail1_h_right)
    road1_h_left.add_traffic_light(l_rail1_h_left)

    # Řadič Přejezdu 1 na road1_h (X=800, Y=350)
    railway_ctrl_1 = RailwayController(
        [rail_v_down, rail_v_up], 
        [l_rail1_h_right, l_rail1_h_left],
        crossing_point=road1_Y # <--- Předáme souřadnici křížení
    )

    # Přejezd 2 na road2_h (X=800, Y=600)
    l_rail2_h_right = TrafficLight(rail1_X - 30)   # Semafor na 770m
    l_rail2_h_left  = TrafficLight(size_width - rail1_X - 30)  # Semafor na 370m

    road2_h_right.add_traffic_light(l_rail2_h_right)
    road2_h_left.add_traffic_light(l_rail2_h_left)

    # Řadič Přejezdu 2 na road2_h (X=800, Y=600)
    railway_ctrl_2 = RailwayController(
        [rail_v_down, rail_v_up],
        [l_rail2_h_right, l_rail2_h_left],
        crossing_point=road2_Y # <--- Předáme souřadnici křížení
    )

    # Přejezd 3 na road_v (X=400, Y=100)
    l_rail_v_down = TrafficLight(rail2_Y - 30)   # Semafor na 70m
    l_rail_v_up   = TrafficLight(size_height - rail2_Y - 30)  # Semafor na 570m

    road_v_down.add_traffic_light(l_rail_v_down)
    road_v_up.add_traffic_light(l_rail_v_up)

    # Řadič Přejezdu 3 na road_v (X=400, Y=100)
    railway_ctrl_3 = RailwayController(
        [rail_h_right, rail_h_left],
        [l_rail_v_down, l_rail_v_up],
        crossing_point=rail2_X # <--- Předáme souřadnici křížení
    )
    
    # --- SPUŠTĚNÍ ---
    roads = [road1_h_right, road1_h_left, road2_h_right, road2_h_left,road_v_down, road_v_up, rail_h_left, rail_h_right, rail_v_down, rail_v_up]
    generator = TrafficGenerator(roads)
    
    app = Visualizer(roads, generator, 1200, 700)
    
    # Visualizeru musíme předat OBA řadiče, aby je aktualizoval
    # Uděláme si na to malý trik - přidáme si je do seznamu
    app.controllers = [smart_intersection_ctrl_1, intersection_ctrl_2, railway_ctrl_1, railway_ctrl_2, railway_ctrl_3]
    
    # Upravíme metodu run ve Visualizeru, aby volala všechny controllery
    # (viz malá úprava níže)
    
    # Rychlý hack: Metoda run ve Visualizeru volá 'self.intersection_ctrl'.
    # Abychom nemuseli přepisovat Visualizer, uděláme objekt, který se tváří jako jeden controller
    class MasterController:
        def __init__(self, ctrls): self.ctrls = ctrls
        def update(self, dt):
            for c in self.ctrls: c.update(dt)
        @property
        def state(self): return "RUNNING" # Dummy
            
    app.intersection_ctrl = MasterController(app.controllers)
    
    app.run()