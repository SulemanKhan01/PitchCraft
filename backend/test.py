# test_part2.py — Run this to verify Part 2 services

# from src.services.website_generator.validator import validate_generated_website
# from src.services.website_generator.deployer import create_in_memory_zip

# files = validate_generated_website({
#     'index_html': '<h1>Welcome to My Test Website, this is a test string</h1>',
#     'styles_css': 'h1 { color: red; font-size: 2rem; }',
#     'script_js': 'console.log("test ok");'
# })

# zip_bytes = create_in_memory_zip(files)

# print('Test 1 PASSED')
# print('Files generated:', list(files.keys()))
# print('ZIP size:', len(zip_bytes), 'bytes')
# print('HTML preview (first 100 chars):', files['index.html'][:100])


# Test 2 — OpenAI Generator
# from src.services.website_generator.generator import generate_website_code

# result = generate_website_code('Create a simple coffee shop website with a hero and contact section')

# print('Test 2 PASSED')
# print('Site title:', result.get('site_title'))
# print('HTML length:', len(result.get('index.html', '')), 'characters')
# print('CSS length:', len(result.get('styles.css', '')), 'characters')
# print('JS length:', len(result.get('script.js', '')), 'characters')


# Test 3 — Netlify Deployer

from src.services.website_generator.deployer import deploy_to_netlify

test_files = {
    'index.html': '<!DOCTYPE html><html><head><title>PitchCraft Test</title></head><body style="font-family:sans-serif;background:#111;color:white;text-align:center;padding:80px"><h1>🚀 Hello from PitchCraft!</h1><p>This website was deployed automatically.</p></body></html>',
    'styles.css': 'body { margin: 0; }',
    'script.js': 'console.log("deployed by PitchCraft!");'
}

result = deploy_to_netlify(test_files)

print('Test 3 PASSED')
print('Public URL:', result['public_url'])
print('Site ID:', result['site_id'])
print('Site Name:', result['site_name'])
