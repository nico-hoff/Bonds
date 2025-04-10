import numpy as np
from scipy import optimize
from typing import Dict, List, Optional, Union

def calculate_ytm(price: float, face_value: float, coupon_rate: float, years_to_maturity: float, 
                 frequency: int = 1) -> float:
    """
    Calculate Yield to Maturity using Newton's method
    
    Args:
        price: Current market price of the bond
        face_value: Face value (par value) of the bond
        coupon_rate: Annual coupon rate as a decimal (e.g., 0.05 for 5%)
        years_to_maturity: Years until bond maturity
        frequency: Coupon payment frequency per year (default: 1 for annual)
        
    Returns:
        Yield to Maturity as a decimal
    """
    # Function to find the zero of (to solve for YTM)
    def bond_price_equation(ytm):
        # Total number of coupon payments
        n_payments = years_to_maturity * frequency
        
        # Coupon payment per period
        coupon_payment = face_value * coupon_rate / frequency
        
        # Calculate present value of all coupon payments and face value
        pv_coupon = 0
        for i in range(1, int(n_payments) + 1):
            pv_coupon += coupon_payment / (1 + ytm / frequency) ** i
        
        pv_face = face_value / (1 + ytm / frequency) ** n_payments
        
        # Return difference between calculated PV and market price
        return pv_coupon + pv_face - price
    
    # Start with an initial guess (coupon rate is usually close to YTM)
    initial_guess = coupon_rate
    
    try:
        # Use scipy's root finding to solve for YTM
        result = optimize.newton(bond_price_equation, initial_guess, tol=1e-6, maxiter=100)
        return max(result, 0)  # YTM shouldn't be negative (though theoretically it can be)
    except:
        # If Newton's method fails, try bisection which is more robust but slower
        try:
            result = optimize.bisect(bond_price_equation, -0.5, 1.0, xtol=1e-6)
            return max(result, 0)
        except:
            # If all fails, return an estimate
            return coupon_rate  # A rough approximation

def real_yield(nominal_yield: float, inflation_rate: float) -> float:
    """
    Calculate real yield using Fisher equation
    
    Args:
        nominal_yield: Nominal yield as a decimal (e.g., 0.05 for 5%)
        inflation_rate: Inflation rate as a decimal (e.g., 0.02 for 2%)
        
    Returns:
        Real yield as a decimal
    """
    # Fisher equation: (1 + r) = (1 + n) / (1 + i)
    real = (1 + nominal_yield) / (1 + inflation_rate) - 1
    return real

def calculate_duration(price: float, face_value: float, coupon_rate: float, 
                      ytm: float, years_to_maturity: float, frequency: int = 1) -> float:
    """
    Calculate Macaulay Duration of a bond
    
    Args:
        price: Current market price of the bond
        face_value: Face value (par value) of the bond
        coupon_rate: Annual coupon rate as a decimal
        ytm: Yield to Maturity as a decimal
        years_to_maturity: Years until bond maturity
        frequency: Coupon payment frequency per year
        
    Returns:
        Macaulay Duration in years
    """
    n_payments = years_to_maturity * frequency
    coupon_payment = face_value * coupon_rate / frequency
    
    # Calculate weighted present values
    total_weighted_pv = 0
    total_pv = 0
    
    for i in range(1, int(n_payments) + 1):
        t = i / frequency  # Time in years
        pv = coupon_payment / (1 + ytm / frequency) ** i
        total_weighted_pv += t * pv
        total_pv += pv
    
    # Add face value at maturity
    t_maturity = n_payments / frequency
    pv_face = face_value / (1 + ytm / frequency) ** n_payments
    total_weighted_pv += t_maturity * pv_face
    total_pv += pv_face
    
    # Macaulay Duration
    duration = total_weighted_pv / total_pv
    
    return duration

def calculate_modified_duration(macaulay_duration: float, ytm: float, frequency: int = 1) -> float:
    """
    Calculate Modified Duration from Macaulay Duration
    
    Args:
        macaulay_duration: Macaulay Duration of the bond in years
        ytm: Yield to Maturity as a decimal
        frequency: Coupon payment frequency per year
        
    Returns:
        Modified Duration
    """
    return macaulay_duration / (1 + ytm / frequency)

def calculate_convexity(price: float, face_value: float, coupon_rate: float,
                      ytm: float, years_to_maturity: float, frequency: int = 1) -> float:
    """
    Calculate convexity of a bond
    
    Args:
        price: Current market price of the bond
        face_value: Face value (par value) of the bond
        coupon_rate: Annual coupon rate as a decimal
        ytm: Yield to Maturity as a decimal
        years_to_maturity: Years until bond maturity
        frequency: Coupon payment frequency per year
        
    Returns:
        Convexity of the bond
    """
    n_payments = years_to_maturity * frequency
    coupon_payment = face_value * coupon_rate / frequency
    
    total_weighted_pv = 0
    total_pv = 0
    
    for i in range(1, int(n_payments) + 1):
        t = i / frequency  # Time in years
        pv = coupon_payment / (1 + ytm / frequency) ** i
        # For convexity, we use t * (t + 1) weighting
        total_weighted_pv += t * (t + 1/frequency) * pv
        total_pv += pv
    
    # Add face value at maturity
    t_maturity = n_payments / frequency
    pv_face = face_value / (1 + ytm / frequency) ** n_payments
    total_weighted_pv += t_maturity * (t_maturity + 1/frequency) * pv_face
    total_pv += pv_face
    
    # Convexity formula
    convexity = total_weighted_pv / (total_pv * (1 + ytm / frequency) ** 2)
    
    return convexity

def get_price_impact(duration: float, convexity: float, yield_change: float) -> float:
    """
    Calculate price impact of yield change using duration and convexity
    
    Args:
        duration: Modified duration of the bond
        convexity: Convexity of the bond
        yield_change: Change in yield in decimal (e.g., 0.01 for 1% increase)
        
    Returns:
        Estimated percent price change
    """
    # First-order approximation using duration
    first_order = -duration * yield_change
    
    # Second-order correction using convexity
    second_order = 0.5 * convexity * (yield_change ** 2)
    
    # Total price change as a percentage
    return (first_order + second_order) * 100 