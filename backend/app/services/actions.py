from ..schemas import ActionDraftRequest

_TEMPLATES = {
    "en": {
        "hotel_late_checkin": (
            "Hello {provider_name}, my journey from {origin} to {destination} has been "
            "disrupted. My revised arrival time is not confirmed yet. Could you please "
            "note a possible late check-in? I will contact you again when I have verified "
            "travel details."
        ),
        "refund_inquiry": (
            "Hello {provider_name}, my journey from {origin} to {destination} was disrupted. "
            "Could you please explain the applicable cancellation and refund options for my "
            "booking? I understand eligibility depends on your policy and the booking terms."
        ),
        "cab_pickup_update": (
            "Hello {provider_name}, my travel from {origin} to {destination} has been disrupted. "
            "The pickup time may need to change, but I do not yet have a confirmed replacement "
            "arrival time. Please let me know how I can update the pickup."
        ),
        "appointment_reschedule": (
            "Hello {provider_name}, travel disruption may affect my planned arrival from "
            "{origin} to {destination}. I cannot confirm a new arrival time yet. Could we "
            "discuss rescheduling my appointment?"
        ),
        "disruption_notification": (
            "Hello {provider_name}, I am contacting you because my journey from {origin} to "
            "{destination} has been disrupted. The travel details are not independently "
            "verified here, and I will share an update after confirming them with the operator."
        ),
    },
    "hi": {
        "hotel_late_checkin": (
            "नमस्ते {provider_name}, {origin} से {destination} की मेरी यात्रा में बाधा आई है। "
            "मेरे पहुँचने का नया समय अभी पक्का नहीं है। क्या आप देर से चेक-इन की संभावना दर्ज "
            "कर सकते हैं? यात्रा की पुष्टि होने पर मैं फिर संपर्क करूँगा/करूँगी।"
        ),
        "refund_inquiry": (
            "नमस्ते {provider_name}, {origin} से {destination} की मेरी यात्रा बाधित हुई है। "
            "कृपया मेरी बुकिंग पर लागू रद्दीकरण और धन-वापसी विकल्प बताएं। मैं समझता/समझती हूँ "
            "कि पात्रता आपकी नीति और बुकिंग की शर्तों पर निर्भर करती है।"
        ),
        "cab_pickup_update": (
            "नमस्ते {provider_name}, {origin} से {destination} की मेरी यात्रा बाधित हुई है। "
            "पिकअप का समय बदलना पड़ सकता है, लेकिन नया पहुँचने का समय अभी पक्का नहीं है। "
            "कृपया बताएं कि पिकअप कैसे अपडेट किया जा सकता है।"
        ),
        "appointment_reschedule": (
            "नमस्ते {provider_name}, यात्रा में बाधा के कारण {origin} से {destination} पहुँचने "
            "में देरी हो सकती है। नया समय अभी पक्का नहीं है। क्या हम अपॉइंटमेंट का नया समय तय "
            "कर सकते हैं?"
        ),
        "disruption_notification": (
            "नमस्ते {provider_name}, {origin} से {destination} की मेरी यात्रा बाधित हुई है। "
            "यहाँ यात्रा की जानकारी स्वतंत्र रूप से सत्यापित नहीं है। ऑपरेटर से पुष्टि के बाद "
            "मैं आपको जानकारी दूँगा/दूँगी।"
        ),
    },
    "kn": {
        "hotel_late_checkin": (
            "ನಮಸ್ಕಾರ {provider_name}, {origin} ನಿಂದ {destination} ಗೆ ನನ್ನ ಪ್ರಯಾಣಕ್ಕೆ ಅಡಚಣೆ "
            "ಉಂಟಾಗಿದೆ. ಹೊಸ ಆಗಮನದ ಸಮಯ ಇನ್ನೂ ಖಚಿತವಾಗಿಲ್ಲ. ತಡವಾಗಿ ಚೆಕ್-ಇನ್ ಆಗುವ ಸಾಧ್ಯತೆಯನ್ನು "
            "ದಯವಿಟ್ಟು ದಾಖಲಿಸಬಹುದೇ? ಪ್ರಯಾಣದ ವಿವರಗಳನ್ನು ಖಚಿತಪಡಿಸಿದ ನಂತರ ಮತ್ತೆ ಸಂಪರ್ಕಿಸುತ್ತೇನೆ."
        ),
        "refund_inquiry": (
            "ನಮಸ್ಕಾರ {provider_name}, {origin} ನಿಂದ {destination} ಗೆ ನನ್ನ ಪ್ರಯಾಣಕ್ಕೆ ಅಡಚಣೆ "
            "ಉಂಟಾಗಿದೆ. ನನ್ನ ಬುಕಿಂಗ್‌ಗೆ ಅನ್ವಯಿಸುವ ರದ್ದತಿ ಮತ್ತು ಮರುಪಾವತಿ ಆಯ್ಕೆಗಳನ್ನು ತಿಳಿಸಬಹುದೇ? "
            "ಅರ್ಹತೆ ನಿಮ್ಮ ನೀತಿ ಮತ್ತು ಬುಕಿಂಗ್ ನಿಯಮಗಳ ಮೇಲೆ ಅವಲಂಬಿತವಾಗಿದೆ ಎಂದು ತಿಳಿದಿದೆ."
        ),
        "cab_pickup_update": (
            "ನಮಸ್ಕಾರ {provider_name}, {origin} ನಿಂದ {destination} ಗೆ ನನ್ನ ಪ್ರಯಾಣಕ್ಕೆ ಅಡಚಣೆ "
            "ಉಂಟಾಗಿದೆ. ಪಿಕಪ್ ಸಮಯ ಬದಲಾಗಬಹುದು, ಆದರೆ ಹೊಸ ಆಗಮನದ ಸಮಯ ಇನ್ನೂ ಖಚಿತವಾಗಿಲ್ಲ. ಪಿಕಪ್ "
            "ಸಮಯವನ್ನು ಹೇಗೆ ನವೀಕರಿಸಬಹುದು ಎಂದು ತಿಳಿಸಿ."
        ),
        "appointment_reschedule": (
            "ನಮಸ್ಕಾರ {provider_name}, ಪ್ರಯಾಣದ ಅಡಚಣೆಯಿಂದ {origin} ನಿಂದ {destination} ಗೆ "
            "ನಿಗದಿತ ಸಮಯಕ್ಕೆ ತಲುಪಲು ಸಾಧ್ಯವಾಗದಿರಬಹುದು. ಹೊಸ ಆಗಮನದ ಸಮಯ ಇನ್ನೂ ಖಚಿತವಿಲ್ಲ. "
            "ಅಪಾಯಿಂಟ್‌ಮೆಂಟ್ ಅನ್ನು ಮರುನಿಗದಿಪಡಿಸಬಹುದೇ?"
        ),
        "disruption_notification": (
            "ನಮಸ್ಕಾರ {provider_name}, {origin} ನಿಂದ {destination} ಗೆ ನನ್ನ ಪ್ರಯಾಣಕ್ಕೆ ಅಡಚಣೆ "
            "ಉಂಟಾಗಿದೆ. ಈ ಪ್ರಯಾಣದ ಮಾಹಿತಿ ಇಲ್ಲಿ ಸ್ವತಂತ್ರವಾಗಿ ಪರಿಶೀಲಿಸಲ್ಪಟ್ಟಿಲ್ಲ. ಆಪರೇಟರ್‌ನಿಂದ "
            "ಖಚಿತಪಡಿಸಿಕೊಂಡ ನಂತರ ನಿಮಗೆ ನವೀಕರಣ ನೀಡುತ್ತೇನೆ."
        ),
    },
}


def draft_action(payload: ActionDraftRequest) -> dict[str, object]:
    content = _TEMPLATES[payload.language][payload.action].format(
        provider_name=payload.provider_name.strip(),
        origin=payload.origin.strip(),
        destination=payload.destination.strip(),
    )
    return {
        "action": payload.action,
        "language": payload.language,
        "provider_name": payload.provider_name.strip(),
        "content": content,
        "source": "StrandedPool editable template",
        "requires_user_review": True,
        "sent": False,
    }
