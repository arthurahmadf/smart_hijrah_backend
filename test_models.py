# test_models.py
import os
import time
from google import genai
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

# Setup Gemini
gemini_client = genai.Client(api_key=os.getenv('GEMINI_API_KEY'))

# Setup Groq
groq_client = Groq(api_key=os.getenv('GROQ_API_KEY'))

# Prompts test
PROMPTS = [
    "Apa hukum puasa Ramadhan?",
    "Jelaskan tentang ikhlas dalam Islam.",
    "Sebutkan rukun Islam.",
]

# ===== MODEL YANG DIUJI =====
# Berdasarkan dokumentasi Groq
MODELS = {
    "gemini": [
        "gemini-2.5-flash",        # Backup 1 (stabil)
        "gemini-2.5-flash-lite",   # Backup 2 (cepat, kadang error)
    ],
    "groq": [
        "llama-3.1-8b-instant",    # ✅ Primary (sudah teruji)
        "openai/gpt-oss-20b",      # ⚡ Tercepat 1000 tps
        "qwen/qwen3-32b",          # 🧠 32B parameter
        "llama-3.3-70b-versatile", # 🔥 70B parameter
        "meta-llama/llama-4-scout-17b-16e-instruct", # 🔬 Preview
    ]
}


def test_gemini(model_name, prompt):
    try:
        start = time.time()
        response = gemini_client.models.generate_content(
            model=model_name,
            contents=prompt,
        )
        elapsed = time.time() - start
        
        return {
            'model': model_name,
            'provider': 'Gemini',
            'response': response.text[:150] + '...' if response.text else '(empty)',
            'time': round(elapsed, 2),
            'success': True,
            'error': None
        }
    except Exception as e:
        return {
            'model': model_name,
            'provider': 'Gemini',
            'response': None,
            'time': None,
            'success': False,
            'error': str(e)
        }


def test_groq(model_name, prompt):
    try:
        start = time.time()
        response = groq_client.chat.completions.create(
            model=model_name,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=512
        )
        elapsed = time.time() - start
        
        return {
            'model': model_name,
            'provider': 'Groq',
            'response': response.choices[0].message.content[:150] + '...',
            'time': round(elapsed, 2),
            'success': True,
            'error': None
        }
    except Exception as e:
        return {
            'model': model_name,
            'provider': 'Groq',
            'response': None,
            'time': None,
            'success': False,
            'error': str(e)
        }


def run_tests():
    print("=" * 80)
    print("MODEL TESTING: GEMINI VS GROQ (DOKUMENTASI RESMI)")
    print("=" * 80)
    
    all_results = []
    
    for prompt_idx, prompt in enumerate(PROMPTS, 1):
        print(f"\n📝 PROMPT {prompt_idx}: {prompt}")
        print("-" * 60)
        
        # Test Gemini
        for model_name in MODELS["gemini"]:
            print(f"  🔄 Gemini: {model_name}...", end="", flush=True)
            result = test_gemini(model_name, prompt)
            all_results.append(result)
            
            if result['success']:
                print(f" ✅ {result['time']}s")
            else:
                error_msg = result['error'][:40] if result['error'] else 'unknown'
                print(f" ❌ {error_msg}...")
        
        # Test Groq
        for model_name in MODELS["groq"]:
            print(f"  🔄 Groq: {model_name}...", end="", flush=True)
            result = test_groq(model_name, prompt)
            all_results.append(result)
            
            if result['success']:
                print(f" ✅ {result['time']}s")
            else:
                error_msg = result['error'][:40] if result['error'] else 'unknown'
                print(f" ❌ {error_msg}...")
    
    # ===== SUMMARY =====
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"{'Model':<40} {'Provider':<10} {'Time':<10} {'Status':<10}")
    print("-" * 80)
    
    for r in all_results:
        status = "✅ OK" if r['success'] else "❌ FAIL"
        time_str = f"{r['time']}s" if r['success'] else "-"
        print(f"{r['model']:<40} {r['provider']:<10} {time_str:<10} {status:<10}")
    
    # ===== REKOMENDASI =====
    print("\n" + "=" * 80)
    print("REKOMENDASI FINAL")
    print("=" * 80)
    
    successful = [r for r in all_results if r['success']]
    
    if successful:
        # Tercepat overall
        fastest = min(successful, key=lambda x: x['time'])
        print(f"⚡ Tercepat: {fastest['model']} ({fastest['time']}s)")
        
        # Groq tercepat
        groq_ok = [r for r in successful if r['provider'] == 'Groq']
        if groq_ok:
            fastest_groq = min(groq_ok, key=lambda x: x['time'])
            print(f"⚡ Groq tercepat: {fastest_groq['model']} ({fastest_groq['time']}s)")
        
        # Paling stabil
        model_counts = {}
        for r in all_results:
            key = r['model']
            if key not in model_counts:
                model_counts[key] = {'total': 0, 'success': 0}
            model_counts[key]['total'] += 1
            if r['success']:
                model_counts[key]['success'] += 1
        
        print("\n📊 Stabilitas:")
        for model, stats in model_counts.items():
            pct = (stats['success'] / stats['total'] * 100) if stats['total'] > 0 else 0
            bar = "█" * int(pct / 10) + "░" * (10 - int(pct / 10))
            print(f"  {model:<40} {bar} {pct:.0f}%")


if __name__ == "__main__":
    run_tests()