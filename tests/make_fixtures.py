"""Regenerate only the public, synthetic fixtures used in tests and screenshots."""
from datetime import datetime, timedelta, timezone
from email.utils import format_datetime
from pathlib import Path

from tests.helpers import mbox, message

ROOT = Path(__file__).parent / "fixtures"

ENTRIES = [
    ("Harbor Rail", "tickets", "Your autumn journey — booking confirmed", "Hi Alex,\n\nYour seat is reserved for the Saturday morning train to the coast.\n\nDeparture: 14 November, 09:24\nArrival: 11:02\nBooking reference: LANTERN-421\nSeat: Coach 4, seat 18A\n\nPlease bring the attached booking note. Have a lovely weekend.\n\nHarbor Rail", "train-booking.txt", b"SYNTHETIC TICKET\nLANTERN-421\n14 November 2026 09:24\nCoach 4 Seat 18A\n"),
    ("Mia Chen", "mia", "A slow Sunday lunch?", "Hi Alex,\n\nLet's have lunch at home this Sunday. I'll bring the bread and olives. Could you make that roasted tomato soup again?\n\nNo rush — around one is perfect.\n\nMia", None, None),
    ("Northfield Workshop", "care", "Your coffee machine warranty is ready", "Hello Alex,\n\nThank you for choosing the Northfield Mini. Your warranty runs until 8 November 2028.\n\nSerial: NF-MINI-2048\nOrder: ORDER-731\n\nKeep this email and the attached warranty note with your purchase receipt.\n\nThe Northfield team", "warranty-NF-MINI.txt", b"SYNTHETIC WARRANTY\nNorthfield Mini\nSerial NF-MINI-2048\nExpires 2028-11-08\n"),
    ("林晓", "lin", "周末的家庭相册", "Alex，\n\n把上周一起散步拍的照片整理好了。小朋友在落叶堆里笑得特别开心。\n\n下次见面带上相机，我们去河边走走。\n\n晓", None, None),
    ("Cedar House", "stay", "Your stay at Cedar House", "Hi Alex,\n\nWe look forward to welcoming you on 14 November. Check-in is from 15:00, and the little reading room is open all afternoon.\n\nRoom: The Willow Room\nReservation: CEDAR-118\n\nLet us know if you need a late arrival.\n\nSam at Cedar House", "reservation-CEDAR-118.txt", b"SYNTHETIC RESERVATION\nCedar House / Willow Room\nArrival 2026-11-14\nDeparture 2026-11-16\n"),
    ("Harbor Library", "library", "Your reserved book is waiting", "Hello Alex,\n\nThe book you reserved, A Field Guide to Small Gardens, is ready to collect. We will hold it until 12 November.\n\nSee you soon,\nHarbor Library", None, None),
    ("Westbound Cycles", "service", "Bicycle service receipt", "Hi Alex,\n\nYour bicycle is ready. We adjusted the brakes, cleaned the drivetrain and replaced the rear cable.\n\nService total: 42.00\nReference: BIKE-104\n\nEnjoy the ride,\nLeah", "bicycle-service.txt", b"SYNTHETIC RECEIPT\nBrake adjustment 18.00\nCable replacement 24.00\nTotal 42.00\n"),
    ("Mum", "family", "The recipe you asked for", "Hi love,\n\nHere is the apple cake recipe: three apples, two eggs, 150 g flour, 100 g butter and a little cinnamon. Bake at 180 C until golden.\n\nIt is even better the next morning.\n\nMum", None, None),
    ("Lakeside Pottery", "studio", "Saturday workshop details", "Hello Alex,\n\nYour place at our hand-building workshop is confirmed for 21 November at 10:00. Aprons and clay are included; bring an old towel if you have one.\n\nWe will start with a small breakfast bowl.\n\nLakeside Pottery", None, None),
    ("City Water", "billing", "October water statement", "Dear Alex,\n\nYour October statement is attached for your records. The balance has been paid.\n\nStatement reference: WATER-2026-10\n\nCustomer care", "water-october.txt", b"SYNTHETIC STATEMENT\nOctober 2026\nUsage 8 cubic meters\nPaid 24.80\n"),
    ("Nora Patel", "nora", "Walking route for next weekend", "Hi Alex,\n\nThe riverside path is open again. Let's start at the old bridge and walk toward the orchard. It's about six kilometres, with a cafe halfway.\n\nI'll bring a thermos.\n\nNora", None, None),
    ("Paper & Pine", "orders", "Your notebook order has shipped", "Hello Alex,\n\nYour two linen notebooks are on their way. We included the refill guide in the package.\n\nOrder: PP-820\n\nThank you for supporting our little shop.\n\nPaper & Pine", None, None),
    ("Lin Xiao", "lin", "保修发票已整理", "Alex，\n\n咖啡机的购买发票和保修说明已经放在附件里。申请维修时，需要提供机器序列号和购买日期。\n\n这是一份合成测试邮件，不包含真实订单。\n\n晓", "保修发票.txt", "合成测试发票\n咖啡机 NF-MINI-2048\n购买日期：2026-10-18\n".encode()),
    ("Garden Club", "garden", "Autumn seed swap", "Dear neighbours,\n\nBring spare seeds to the community garden on 7 November. Envelopes, labels and tea will be provided. Beginners are very welcome.\n\nThe garden volunteers", None, None),
    ("Coastline Ferry", "ferry", "Your ferry reservation", "Hello Alex,\n\nYour crossing is booked for 15 November at 10:30. Please arrive twenty minutes before departure.\n\nReservation: FERRY-612\nPassengers: 2 adults\n\nSafe travels.", "ferry-note.txt", b"SYNTHETIC FERRY BOOKING\nFERRY-612\n15 November 2026 / 10:30\n"),
    ("Mia Chen", "mia", "That little bookshop", "Hi Alex,\n\nI found the bookshop we talked about. They have a whole shelf of nature writing and a very sleepy cat. Let's stop by when we are in the neighbourhood.\n\nMia", None, None),
    ("Atelier Frames", "frames", "Your print is ready to collect", "Hello Alex,\n\nThe oak frame for your landscape print is finished. We are open until six on weekdays and four on Saturdays.\n\nOrder: FRAME-930\n\nThank you,\nAtelier Frames", None, None),
    ("Community Hall", "events", "November film evening", "Hello everyone,\n\nOur next film evening is on 20 November. Doors open at 18:30. Bring a cushion if you like; refreshments are by donation.\n\nSee you there,\nThe hall team", None, None),
    ("Northfield Workshop", "care", "A quick care guide for your coffee machine", "Hi Alex,\n\nA few simple habits will keep your machine happy: rinse the basket after each use, empty the drip tray daily, and descale when the indicator appears.\n\nEnjoy your morning coffee.\n\nNorthfield Workshop", None, None),
    ("Alex Morgan", "alex", "Notes for a quieter November", "Remember:\n\nKeep one weekend free.\nFinish the library book.\nTake the coastal train.\nMake apple cake.\n\nSmall plans are enough.", None, None),
]


def main():
    ROOT.mkdir(parents=True, exist_ok=True)
    start = datetime(2026, 11, 9, 9, 42, tzinfo=timezone(timedelta(hours=8)))
    messages = []
    for index, (name, address, subject, body, filename, payload) in enumerate(ENTRIES):
        messages.append(message(subject, body, sender=f"{name} <{address}@example.com>", date=format_datetime(start - timedelta(hours=index * 11)), message_id=f"<mailcairn-synthetic-{index + 1:03d}@example.com>", attachment=(filename, payload) if filename else None, crlf=index % 2 == 0))
    (ROOT / "sample.mbox").write_bytes(mbox(*messages))
    (ROOT / "sample.eml").write_bytes(messages[0])
    (ROOT / "invalid.mbox").write_bytes(b"This is deliberately not an MBOX file.\n")
    (ROOT / "empty.mbox").write_bytes(b"")
    print(f"Wrote {len(messages)} synthetic messages to {ROOT}")


if __name__ == "__main__":
    main()
