package main

import (
	"encoding/json"
	"fmt"
	"math"
	"net/http"
	"sync"
)

type Moto struct {
	ID      string `json:"id"`
	Statut  string `json:"statut"`
	Commune string `json:"commune"`
}

var (
	mu       sync.RWMutex
	motos    = make(map[string]Moto)
	communes = []string{"Gombe", "Limete", "Ngaliema", "Bandalungwa", "Kintambo"}
)

func init() {
	// Initialisation de 500 motos-taxis en memoire (RAM)
	for i := 1; i <= 500; i++ {
		id := fmt.Sprintf("moto-%d", i)
		statut := "en_course"
		if i%2 == 0 {
			statut = "libre"
		}
		motos[id] = Moto{
			ID:      id,
			Statut:  statut,
			Commune: communes[i%5],
		}
	}
}

func main() {
	// 1. Mettre a jour le statut d'une moto
	http.HandleFunc("/status", func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("Content-Type", "application/json")
		if r.Method != http.MethodPost {
			w.WriteHeader(http.StatusMethodNotAllowed)
			return
		}
		var data Moto
		if err := json.NewDecoder(r.Body).Decode(&data); err != nil || data.ID == "" || data.Statut == "" || data.Commune == "" {
			w.WriteHeader(http.StatusBadRequest)
			json.NewEncoder(w).Encode(map[string]string{"error": "Donnees incompletes"})
			return
		}
		mu.Lock()
		motos[data.ID] = data
		mu.Unlock()

		w.WriteHeader(http.StatusCreated)
		json.NewEncoder(w).Encode(map[string]string{
			"status":  "ok",
			"id":      data.ID,
			"statut":  data.Statut,
			"commune": data.Commune,
		})
	})

	// 2. Lister et filtrer les motos par commune
	http.HandleFunc("/motos", func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("Content-Type", "application/json")
		if r.Method != http.MethodGet {
			w.WriteHeader(http.StatusMethodNotAllowed)
			return
		}
		commune := r.URL.Query().Get("commune")
		liste := make([]Moto, 0)

		mu.RLock()
		for _, m := range motos {
			if commune == "" || m.Commune == commune {
				liste = append(liste, m)
			}
		}
		mu.RUnlock()

		communeLabel := "Toutes"
		if commune != "" {
			communeLabel = commune
		}
		json.NewEncoder(w).Encode(map[string]interface{}{
			"commune": communeLabel,
			"count":   len(liste),
			"motos":   liste,
		})
	})

	// 3. Calculer les statistiques globales de disponibilite de la flotte
	http.HandleFunc("/stats", func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("Content-Type", "application/json")
		if r.Method != http.MethodGet {
			w.WriteHeader(http.StatusMethodNotAllowed)
			return
		}
		libres := 0
		enCourse := 0

		mu.RLock()
		total := len(motos)
		for _, m := range motos {
			if m.Statut == "libre" {
				libres++
			} else {
				enCourse++
			}
		}
		mu.RUnlock()

		taux := 0.0
		if total > 0 {
			taux = math.Round((float64(libres)/float64(total))*10000) / 100
		}
		json.NewEncoder(w).Encode(map[string]interface{}{
			"total":              total,
			"libres":             libres,
			"en_course":          enCourse,
			"taux_disponibilite": taux,
		})
	})

	fmt.Println("Serveur Go demarre sur http://127.0.0.1:3003")
	http.ListenAndServe("127.0.0.1:3003", nil)
}
