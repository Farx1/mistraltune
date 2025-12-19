#!/usr/bin/env python3
"""
Script d'inférence et comparaison de modèles via l'API Mistral

Ce script permet de:
1. Comparer les réponses du modèle de base vs modèle fine-tuné
2. Tester plusieurs prompts et afficher les résultats côte à côte
3. Calculer des métriques de comparaison (similarité, longueur, etc.)

Usage:
    python src/mistral_api_inference.py --base_model open-mistral-7b --fine_tuned_model ft:open-mistral-7b:XXX

Exemple:
    python src/mistral_api_inference.py \
        --base_model open-mistral-7b \
        --fine_tuned_model ft:open-mistral-7b:XXX:20240430:XXX \
        --prompts "Qu'est-ce que le PTO?" "Define KPI in one sentence."
"""

import argparse
import os
import json
from typing import List, Dict, Any, Optional
from pathlib import Path

from mistralai import Mistral
from mistralai.models import ChatCompletionResponse


def generate_response(
    client: Mistral,
    model: str,
    prompt: str,
    temperature: float = 0.7,
    max_tokens: int = 512,
) -> Dict[str, Any]:
    """
    Génère une réponse avec un modèle via l'API Mistral.
    
    Args:
        client: Client Mistral initialisé
        model: Nom du modèle à utiliser
        prompt: Prompt à envoyer
        temperature: Température pour la génération
        max_tokens: Nombre maximum de tokens à générer
        
    Returns:
        Dictionnaire avec la réponse et les métriques
    """
    try:
        response = client.chat.complete(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            temperature=temperature,
            max_tokens=max_tokens,
        )
        
        content = response.choices[0].message.content
        usage = response.usage
        
        return {
            "content": content,
            "prompt_tokens": usage.prompt_tokens if usage else 0,
            "completion_tokens": usage.completion_tokens if usage else 0,
            "total_tokens": usage.total_tokens if usage else 0,
            "error": None,
        }
    except Exception as e:
        return {
            "content": None,
            "prompt_tokens": 0,
            "completion_tokens": 0,
            "total_tokens": 0,
            "error": str(e),
        }


def compare_responses(
    client: Mistral,
    base_model: str,
    fine_tuned_model: str,
    prompts: List[str],
    temperature: float = 0.7,
    max_tokens: int = 512,
) -> List[Dict[str, Any]]:
    """
    Compare les réponses de deux modèles sur une liste de prompts.
    
    Args:
        client: Client Mistral initialisé
        base_model: Nom du modèle de base
        fine_tuned_model: Nom du modèle fine-tuné
        prompts: Liste des prompts à tester
        temperature: Température pour la génération
        max_tokens: Nombre maximum de tokens à générer
        
    Returns:
        Liste de dictionnaires avec les comparaisons
    """
    results = []
    
    for i, prompt in enumerate(prompts, 1):
        print(f"\n[{i}/{len(prompts)}] Test du prompt: {prompt[:60]}...")
        
        # Générer avec le modèle de base
        print("  Génération avec le modèle de base...")
        base_response = generate_response(
            client, base_model, prompt, temperature, max_tokens
        )
        
        # Générer avec le modèle fine-tuné
        print("  Génération avec le modèle fine-tuné...")
        ft_response = generate_response(
            client, fine_tuned_model, prompt, temperature, max_tokens
        )
        
        # Calculer des métriques de comparaison
        base_len = len(base_response["content"]) if base_response["content"] else 0
        ft_len = len(ft_response["content"]) if ft_response["content"] else 0
        
        results.append({
            "prompt": prompt,
            "base_model": base_model,
            "fine_tuned_model": fine_tuned_model,
            "base_response": base_response["content"],
            "ft_response": ft_response["content"],
            "base_error": base_response["error"],
            "ft_error": ft_response["error"],
            "base_tokens": base_response["total_tokens"],
            "ft_tokens": ft_response["total_tokens"],
            "base_length": base_len,
            "ft_length": ft_len,
            "length_diff": ft_len - base_len,
        })
        
        print(f"  ✓ Comparaison terminée")
    
    return results


def print_comparison(results: List[Dict[str, Any]], detailed: bool = False):
    """
    Affiche les résultats de comparaison de manière formatée.
    
    Args:
        results: Liste des résultats de comparaison
        detailed: Si True, affiche les détails complets
    """
    print("\n" + "="*80)
    print("RÉSULTATS DE COMPARAISON")
    print("="*80)
    
    for i, result in enumerate(results, 1):
        print(f"\n{'─'*80}")
        print(f"Prompt {i}: {result['prompt']}")
        print(f"{'─'*80}")
        
        if result["base_error"]:
            print(f"\n✗ Modèle de base - Erreur: {result['base_error']}")
        else:
            print(f"\n📌 Modèle de base ({result['base_model']}):")
            print(f"   Tokens: {result['base_tokens']} | Longueur: {result['base_length']} caractères")
            if detailed:
                print(f"   Réponse: {result['base_response']}")
            else:
                preview = result['base_response'][:200] if result['base_response'] else "N/A"
                print(f"   Réponse: {preview}{'...' if len(result['base_response'] or '') > 200 else ''}")
        
        if result["ft_error"]:
            print(f"\n✗ Modèle fine-tuné - Erreur: {result['ft_error']}")
        else:
            print(f"\n✨ Modèle fine-tuné ({result['fine_tuned_model']}):")
            print(f"   Tokens: {result['ft_tokens']} | Longueur: {result['ft_length']} caractères")
            if detailed:
                print(f"   Réponse: {result['ft_response']}")
            else:
                preview = result['ft_response'][:200] if result['ft_response'] else "N/A"
                print(f"   Réponse: {preview}{'...' if len(result['ft_response'] or '') > 200 else ''}")
        
        if not result["base_error"] and not result["ft_error"]:
            diff = result['length_diff']
            diff_pct = (diff / result['base_length'] * 100) if result['base_length'] > 0 else 0
            print(f"\n📊 Différence: {diff:+d} caractères ({diff_pct:+.1f}%)")
    
    # Statistiques globales
    print(f"\n{'='*80}")
    print("STATISTIQUES GLOBALES")
    print(f"{'='*80}")
    
    successful = [r for r in results if not r["base_error"] and not r["ft_error"]]
    if successful:
        avg_base_tokens = sum(r["base_tokens"] for r in successful) / len(successful)
        avg_ft_tokens = sum(r["ft_tokens"] for r in successful) / len(successful)
        avg_base_len = sum(r["base_length"] for r in successful) / len(successful)
        avg_ft_len = sum(r["ft_length"] for r in successful) / len(successful)
        
        print(f"Comparaisons réussies: {len(successful)}/{len(results)}")
        print(f"Tokens moyens - Base: {avg_base_tokens:.1f} | Fine-tuné: {avg_ft_tokens:.1f}")
        print(f"Longueur moyenne - Base: {avg_base_len:.1f} | Fine-tuné: {avg_ft_len:.1f}")
        print(f"Différence moyenne: {avg_ft_len - avg_base_len:+.1f} caractères")


def save_results(results: List[Dict[str, Any]], output_file: str):
    """
    Sauvegarde les résultats dans un fichier JSON.
    
    Args:
        results: Liste des résultats de comparaison
        output_file: Chemin vers le fichier de sortie
    """
    output_path = Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    print(f"\n✓ Résultats sauvegardés dans: {output_file}")


def load_prompts_from_file(file_path: str) -> List[str]:
    """
    Charge des prompts depuis un fichier JSONL (format instruction).
    
    Args:
        file_path: Chemin vers le fichier JSONL
        
    Returns:
        Liste des prompts (instructions)
    """
    prompts = []
    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line:
                data = json.loads(line)
                prompt = data.get("instruction", "")
                if prompt:
                    prompts.append(prompt)
    return prompts


def main():
    parser = argparse.ArgumentParser(
        description="Comparaison de modèles via l'API Mistral",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    
    # Modèles
    parser.add_argument("--base_model", required=True, help="Nom du modèle de base (ex: open-mistral-7b)")
    parser.add_argument("--fine_tuned_model", required=True, help="Nom du modèle fine-tuné (ex: ft:open-mistral-7b:XXX)")
    
    # Prompts
    parser.add_argument("--prompts", nargs="+", help="Liste de prompts à tester")
    parser.add_argument("--prompts_file", help="Fichier JSONL avec des prompts (format instruction)")
    
    # Options de génération
    parser.add_argument("--temperature", type=float, default=0.7, help="Température (défaut: 0.7)")
    parser.add_argument("--max_tokens", type=int, default=512, help="Nombre max de tokens (défaut: 512)")
    
    # Sortie
    parser.add_argument("--output", help="Fichier JSON pour sauvegarder les résultats")
    parser.add_argument("--detailed", action="store_true", help="Afficher les réponses complètes")
    
    args = parser.parse_args()
    
    # Vérifier la clé API
    api_key = os.getenv("MISTRAL_API_KEY")
    if not api_key:
        raise ValueError(
            "MISTRAL_API_KEY non définie. "
            "Définissez-la avec: export MISTRAL_API_KEY='votre-clé'"
        )
    
    # Charger les prompts
    if args.prompts:
        prompts = args.prompts
    elif args.prompts_file:
        prompts = load_prompts_from_file(args.prompts_file)
    else:
        # Prompts par défaut pour tester
        prompts = [
            "Qu'est-ce que le PTO ?",
            "Define KPI in one sentence.",
            "Explique le concept de burn rate en startup.",
        ]
        print("⚠ Aucun prompt fourni, utilisation de prompts par défaut")
    
    if not prompts:
        raise ValueError("Aucun prompt à tester")
    
    print(f"Comparaison de {len(prompts)} prompt(s)")
    print(f"  Modèle de base: {args.base_model}")
    print(f"  Modèle fine-tuné: {args.fine_tuned_model}")
    
    # Initialiser le client
    client = Mistral(api_key=api_key)
    
    # Comparer les modèles
    results = compare_responses(
        client,
        args.base_model,
        args.fine_tuned_model,
        prompts,
        temperature=args.temperature,
        max_tokens=args.max_tokens,
    )
    
    # Afficher les résultats
    print_comparison(results, detailed=args.detailed)
    
    # Sauvegarder si demandé
    if args.output:
        save_results(results, args.output)


if __name__ == "__main__":
    main()

