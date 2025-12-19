# Makefile pour le projet Mistral-7B QLoRA Domain QA
# Commandes pratiques pour l'entraînement, l'évaluation et le reporting

.PHONY: help setup demo train-r16 train-r8 train-r32 eval-base eval-r16 eval-r8 eval-r32 plots report clean

# Default target
help:
	@echo "MistralTune - Available commands:"
	@echo ""
	@echo "Setup:"
	@echo "  setup        Create virtual environment and install dependencies"
	@echo ""
	@echo "Demo:"
	@echo "  demo         Run end-to-end demo: train (tiny) → eval → inference"
	@echo ""
	@echo "Training:"
	@echo "  train-r16    Train with LoRA r=16, alpha=32"
	@echo "  train-r8     Train with LoRA r=8, alpha=16"
	@echo "  train-r32    Train with LoRA r=32, alpha=64"
	@echo ""
	@echo "Evaluation:"
	@echo "  eval-base    Evaluate base model Mistral-7B-Instruct"
	@echo "  eval-r16     Evaluate LoRA model r=16, alpha=32"
	@echo "  eval-r8      Evaluate LoRA model r=8, alpha=16"
	@echo "  eval-r32     Evaluate LoRA model r=32, alpha=64"
	@echo ""
	@echo "Reporting:"
	@echo "  plots        Generate performance plots"
	@echo "  report       Generate final report"
	@echo ""
	@echo "Utilities:"
	@echo "  clean        Clean generated files"
	@echo "  help         Show this help"

# Setup virtual environment and install dependencies
setup:
	@echo "Setting up virtual environment..."
	python -m venv .venv
	@echo "Installing dependencies..."
	.venv\Scripts\pip install -r requirements.txt
	@echo "Setup complete! Activate with: .venv\Scripts\activate"

# Demo: quick end-to-end test
demo:
	@echo "Running demo: train (tiny) → eval → inference"
	@bash scripts/demo.sh || cmd /c scripts\demo.bat

# Commandes d'entrainement
train-r16:
	@echo "Entrainement avec LoRA r=16, alpha=32..."
	python src/train_qlora.py --config configs/base.yaml --lora configs/lora_r16a32.yaml --run_id r16a32

train-r8:
	@echo "Entrainement avec LoRA r=8, alpha=16..."
	python src/train_qlora.py --config configs/base.yaml --lora configs/lora_r8a16.yaml --run_id r8a16

train-r32:
	@echo "Entrainement avec LoRA r=32, alpha=64..."
	python src/train_qlora.py --config configs/base.yaml --lora configs/lora_r32a64.yaml --run_id r32a64

# Commandes d'evaluation
eval-base:
	@echo "Evaluation du modele de base..."
	python src/eval_em_f1.py --model_path mistralai/Mistral-7B-Instruct-v0.3 --eval_file data/val.jsonl --save_results
	python src/eval_latency.py --model_path mistralai/Mistral-7B-Instruct-v0.3 --eval_file data/val.jsonl --update_csv

eval-r16:
	@echo "Evaluation du modele LoRA r=16, alpha=32..."
	python src/eval_em_f1.py --model_path runs/mistral7b_qlora_domainqa_r16a32 --eval_file data/val.jsonl --is_adapter --save_results
	python src/eval_latency.py --model_path runs/mistral7b_qlora_domainqa_r16a32 --eval_file data/val.jsonl --is_adapter --update_csv

eval-r8:
	@echo "Evaluation du modele LoRA r=8, alpha=16..."
	python src/eval_em_f1.py --model_path runs/mistral7b_qlora_domainqa_r8a16 --eval_file data/val.jsonl --is_adapter --save_results
	python src/eval_latency.py --model_path runs/mistral7b_qlora_domainqa_r8a16 --eval_file data/val.jsonl --is_adapter --update_csv

eval-r32:
	@echo "Evaluation du modele LoRA r=32, alpha=64..."
	python src/eval_em_f1.py --model_path runs/mistral7b_qlora_domainqa_r32a64 --eval_file data/val.jsonl --is_adapter --save_results
	python src/eval_latency.py --model_path runs/mistral7b_qlora_domainqa_r32a64 --eval_file data/val.jsonl --is_adapter --update_csv

# Generer les graphiques depuis les resultats
plots:
	@echo "Generation des graphiques de performance..."
	python -c "import matplotlib.pyplot as plt; import pandas as pd; import os; \
		if os.path.exists('reports/results.csv'): \
			df = pd.read_csv('reports/results.csv'); \
			fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5)); \
			df.plot(x='run_id', y=['em', 'f1'], kind='bar', ax=ax1); \
			ax1.set_title('Scores EM et F1'); ax1.set_ylabel('Score'); \
			df.plot(x='run_id', y=['latency_p50', 'latency_p95'], kind='bar', ax=ax2); \
			ax2.set_title('Latence (secondes)'); ax2.set_ylabel('Secondes'); \
			plt.tight_layout(); \
			os.makedirs('reports/figures', exist_ok=True); \
			plt.savefig('reports/figures/comparaison_performance.png', dpi=300, bbox_inches='tight'); \
			plt.close(); \
			print('Graphiques sauvegardes dans reports/figures/comparaison_performance.png'); \
		else: \
			print('Pas de results.csv trouve. Lancez d''abord l''evaluation.')"

# Generer le rapport final
report:
	@echo "Generation du rapport final..."
	python -c "import pandas as pd; import os; \
		if os.path.exists('reports/results.csv'): \
			df = pd.read_csv('reports/results.csv'); \
			report = f'''# Rapport Mistral-7B QLoRA Domain QA\n\n'; \
			report += f'## Resume\n\n'; \
			report += f'Ce rapport resume les performances du fine-tuning QLoRA sur Mistral-7B-Instruct pour des taches de question-reponse specifiques au domaine.\n\n'; \
			report += f'## Resultats\n\n'; \
			report += f'| Modele | EM | F1 | Latence p50 | Latence p95 |\n'; \
			report += f'|--------|----|----|-------------|-------------|\n'; \
			for _, row in df.iterrows(): \
				report += f'| {row[\"run_id\"]} | {row[\"em\"]:.3f} | {row[\"f1\"]:.3f} | {row[\"latency_p50\"]:.3f}s | {row[\"latency_p95\"]:.3f}s |\n'; \
			report += f'\n## Analyse\n\n'; \
			best_em = df.loc[df[\"em\"].idxmax()]; \
			best_f1 = df.loc[df[\"f1\"].idxmax()]; \
			fastest = df.loc[df[\"latency_p95\"].idxmin()]; \
			report += f'- **Meilleur score EM**: {best_em[\"run_id\"]} ({best_em[\"em\"]:.3f})\n'; \
			report += f'- **Meilleur score F1**: {best_f1[\"run_id\"]} ({best_f1[\"f1\"]:.3f})\n'; \
			report += f'- **Plus rapide**: {fastest[\"run_id\"]} ({fastest[\"latency_p95\"]:.3f}s p95)\n\n'; \
			report += f'## Conclusion\n\n'; \
			report += f'Le fine-tuning QLoRA montre des ameliorations par rapport au modele de base. La configuration optimale depend du compromis entre precision et vitesse d''inference.\n'; \
			with open('reports/report.md', 'w') as f: \
				f.write(report); \
			print('Rapport sauvegarde dans reports/report.md'); \
		else: \
			print('Pas de results.csv trouve. Lancez d''abord l''evaluation.')"

# Nettoyer les fichiers generes
clean:
	@echo "Nettoyage des fichiers generes..."
	rmdir /s /q runs 2>nul || echo "Pas de dossier runs a nettoyer"
	rmdir /s /q reports\figures 2>nul || echo "Pas de dossier figures a nettoyer"
	del reports\results.csv 2>nul || echo "Pas de results.csv a nettoyer"
	del reports\report.md 2>nul || echo "Pas de report.md a nettoyer"
	@echo "Nettoyage termine"

# Pipeline complet: entrainer tous les modeles et evaluer
full-pipeline: train-r16 train-r8 train-r32 eval-base eval-r16 eval-r8 eval-r32 plots report
	@echo "Pipeline complet termine !"

# Test rapide: entrainer un modele et evaluer
quick-test: train-r16 eval-base eval-r16 plots report
	@echo "Test rapide termine !"