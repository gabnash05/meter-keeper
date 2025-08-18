import cv2
import pytesseract
import numpy as np

ALLOWED_EXTENSIONS = {'bmp', 'jpg', 'jpeg', 'png', 'tiff', 'tif', 'pnm'}

def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS
def preprocess_image(image_path):
    """Enhanced preprocessing for meter images"""
    # Read image
    img = cv2.imread(image_path, cv2.IMREAD_COLOR)
    if img is None:
        raise ValueError("Could not read image file")

    # Convert to grayscale
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    
    # Adaptive thresholding - better for uneven lighting
    thresh = cv2.adaptiveThreshold(
        gray, 255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY_INV, 11, 2
    )
    
    # Morphological operations to clean up noise
    kernel = np.ones((2, 2), np.uint8)
    processed = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)
    
    return processed

def extract_kwh(image_path):
    """Improved digit extraction with error handling"""
    try:
        # Preprocess with error handling
        processed = preprocess_image(image_path)
        
        # Custom OCR configuration for digital displays
        custom_config = (
            r'--oem 3 --psm 6 '
            r'-c tessedit_char_whitelist=0123456789 '
            r'-c tessedit_do_invert=1 '
            r'-c textord_heavy_nr=1'
        )
        
        # Run OCR
        text = pytesseract.image_to_string(processed, config=custom_config)
        
        # Extract digits
        digits = ''.join(c for c in text if c.isdigit())
        
        if not digits:
            # Try alternative preprocessing if no digits found
            alt_processed = alternative_preprocess(image_path)
            text = pytesseract.image_to_string(alt_processed, config=custom_config)
            digits = ''.join(c for c in text if c.isdigit())
            if not digits:
                raise ValueError("No digits detected after multiple attempts")
                
        return float(digits[:8])  # Limit to reasonable digit length
        
    except Exception as e:
        raise ValueError(f"OCR processing failed: {str(e)}")

def alternative_preprocess(image_path):
    """Fallback preprocessing method"""
    img = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
    _, processed = cv2.threshold(img, 120, 255, cv2.THRESH_BINARY)
    return processed