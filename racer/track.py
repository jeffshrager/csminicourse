from PIL import Image
import numpy as np

def png_screenshot_to_binary_matrix(image_path, threshold=128):
    """
    Convert a PNG screenshot to a binary matrix where black=1 and white=0.
    
    Args:
        image_path (str): Path to the PNG screenshot
        threshold (int): Threshold value (0-255) for binary conversion
                        Pixels darker than this become 1, lighter become 0
    
    Returns:
        numpy.ndarray: MxN binary matrix (original dimensions)
    """
    # Open and load the PNG image
    image = Image.open(image_path)
    
    # Handle transparency if present (PNG can have alpha channel)
    if image.mode == 'RGBA':
        # Convert RGBA to RGB by compositing over white background
        background = Image.new('RGB', image.size, (255, 255, 255))
        background.paste(image, mask=image.split()[-1])  # Use alpha channel as mask
        image = background
    elif image.mode == 'LA':
        # Convert LA (grayscale with alpha) to L
        background = Image.new('L', image.size, 255)
        background.paste(image, mask=image.split()[-1])
        image = background
    
    # Convert to grayscale if it's not already
    if image.mode != 'L':
        image = image.convert('L')
    
    # Convert to numpy array
    img_array = np.array(image)
    
    # Create binary matrix: pixels darker than threshold become 1, others become 0
    binary_matrix = (img_array < threshold).astype(int)
    
    return binary_matrix

def resize_screenshot_to_square(image_path, size, threshold=128):
    """
    Resize PNG screenshot to MxM and convert to binary matrix.
    
    Args:
        image_path (str): Path to the PNG screenshot
        size (int): Desired size for MxM matrix
        threshold (int): Threshold for binary conversion
    
    Returns:
        numpy.ndarray: MxM binary matrix
    """
    image = Image.open(image_path)
    
    # Handle transparency
    if image.mode == 'RGBA':
        background = Image.new('RGB', image.size, (255, 255, 255))
        background.paste(image, mask=image.split()[-1])
        image = background
    elif image.mode == 'LA':
        background = Image.new('L', image.size, 255)
        background.paste(image, mask=image.split()[-1])
        image = background
    
    # Resize to square (screenshots are often rectangular)
    image = image.resize((size, size), Image.Resampling.LANCZOS)
    
    # Convert to grayscale
    if image.mode != 'L':
        image = image.convert('L')
    
    # Convert to numpy array and apply threshold
    img_array = np.array(image)
    binary_matrix = (img_array < threshold).astype(int)
    
    return binary_matrix

def adaptive_threshold_screenshot(image_path, method='otsu'):
    """
    Use adaptive thresholding for better results with screenshots.
    
    Args:
        image_path (str): Path to the PNG screenshot
        method (str): 'otsu' or 'mean' for thresholding method
    
    Returns:
        numpy.ndarray: Binary matrix with adaptive threshold
    """
    image = Image.open(image_path)
    
    # Handle transparency
    if image.mode == 'RGBA':
        background = Image.new('RGB', image.size, (255, 255, 255))
        background.paste(image, mask=image.split()[-1])
        image = background
    
    # Convert to grayscale
    if image.mode != 'L':
        image = image.convert('L')
    
    img_array = np.array(image)
    
    if method == 'otsu':
        # Simple Otsu's method implementation
        hist, _ = np.histogram(img_array.flatten(), bins=256, range=(0, 256))
        total_pixels = img_array.size
        
        best_threshold = 0
        best_variance = 0
        
        for t in range(256):
            w0 = np.sum(hist[:t])
            w1 = np.sum(hist[t:])
            
            if w0 == 0 or w1 == 0:
                continue
                
            mu0 = np.sum(np.arange(t) * hist[:t]) / w0
            mu1 = np.sum(np.arange(t, 256) * hist[t:]) / w1
            
            variance = w0 * w1 * (mu0 - mu1) ** 2
            
            if variance > best_variance:
                best_variance = variance
                best_threshold = t
        
        threshold = best_threshold
    else:  # method == 'mean'
        threshold = np.mean(img_array)
    
    print(f"Adaptive threshold: {threshold:.1f}")
    binary_matrix = (img_array < threshold).astype(int)
    
    return binary_matrix

# Example usage
if __name__ == "__main__":
    # Screenshot path
    screenshot_path = "track1.png"
    print(screenshot_path)
    try:
        # Method 1: Convert screenshot as-is
        binary_matrix = png_screenshot_to_binary_matrix(screenshot_path)
        
        print(f"Screenshot dimensions: {binary_matrix.shape}")
        print("Sample of binary matrix (top-left 10x10):")
        print(binary_matrix)
        
        # Method 2: Resize to specific MxM size
        M = 50  # Common size for screenshots
        square_matrix = resize_screenshot_to_square(screenshot_path, M)
        
        print(f"\nResized to {M}x{M}:")
        print(square_matrix.shape)
        
        import json

        # Convert numpy array to regular Python list and save as JSON
        matrix_list = square_matrix.tolist()
        with open("square_matrix.json", "w") as f:
            json.dump(matrix_list, f)

        print("Matrix saved to square_matrix.json")

        # Method 3: Adaptive thresholding (often better for screenshots)
        adaptive_matrix = adaptive_threshold_screenshot(screenshot_path, method='otsu')
        
        print(f"\nAdaptive threshold result: {adaptive_matrix.shape}")
        
        # Save results
        np.savetxt("screenshot_binary_matrix.txt", binary_matrix, fmt='%d')
        np.savetxt(f"screenshot_binary_{M}x{M}.txt", square_matrix, fmt='%d')
        
        # Visualize the results
        import matplotlib.pyplot as plt
        
        plt.figure(figsize=(15, 5))
        
        # Original screenshot
        plt.subplot(1, 4, 1)
        original_img = Image.open(screenshot_path)
        plt.imshow(original_img)
        plt.title('Original Screenshot')
        plt.axis('off')
        
        # Binary conversion (original size)
        plt.subplot(1, 4, 2)
        plt.imshow(binary_matrix, cmap='gray')
        plt.title('Binary Matrix\n(Original Size)')
        plt.axis('off')
        
        # Resized square
        plt.subplot(1, 4, 3)
        plt.imshow(square_matrix, cmap='gray')
        plt.title(f'Resized to {M}x{M}')
        plt.axis('off')
        
        # Adaptive threshold
        plt.subplot(1, 4, 4)
        plt.imshow(adaptive_matrix, cmap='gray')
        plt.title('Adaptive Threshold')
        plt.axis('off')
        
        plt.tight_layout()
        plt.show()
        
        # Print some statistics
        print(f"\nStatistics:")
        print(f"Total pixels: {binary_matrix.size}")
        print(f"Black pixels (1s): {np.sum(binary_matrix)}")
        print(f"White pixels (0s): {binary_matrix.size - np.sum(binary_matrix)}")
        print(f"Percentage black: {np.sum(binary_matrix) / binary_matrix.size * 100:.1f}%")
        
    except FileNotFoundError:
        print(f"Error: Screenshot file '{screenshot_path}' not found.")
        print("Please make sure the PNG screenshot exists in the current directory.")
    except Exception as e:
        print(f"Error processing screenshot: {e}")
