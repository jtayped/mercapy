import requests
from collections import deque
import concurrent.futures


# Function to get warehouse code for a given postal code
def get_warehouse_code(postal_code):
    url = "https://tienda.mercadona.es/api/postal-codes/actions/change-pc/"
    payload = {"new_postal_code": postal_code}
    headers = {"Content-Type": "application/json"}

    try:
        response = requests.put(url, json=payload, headers=headers)
        if response.status_code == 200:
            return response.headers.get("X-Customer-Wh")
    except Exception as e:
        print(f"Error for postal code {postal_code}: {e}")
    return None


# Function to get neighboring postal codes
def get_neighboring_postal_codes(postal_code):
    neighbors = set()
    postal_code_digits = list(postal_code)
    for i in range(5):
        original_digit = postal_code_digits[i]
        for change in [-1, 1]:
            new_digit = (int(original_digit) + change) % 10
            postal_code_digits[i] = str(new_digit)
            neighbors.add("".join(postal_code_digits))
        postal_code_digits[i] = original_digit
    return neighbors


# BFS to explore postal codes and find unique warehouses
def find_unique_warehouses(starting_postal_codes):
    visited = set()
    unique_warehouses = set()
    queue = deque(starting_postal_codes)
    total_checked = 0

    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        futures = []
        while queue:
            current_postal_code = queue.popleft()
            if current_postal_code in visited:
                continue

            visited.add(current_postal_code)
            total_checked += 1
            print(
                f"Checking postal code: {current_postal_code} (Total checked: {total_checked})"
            )

            futures.append(executor.submit(get_warehouse_code, current_postal_code))

            # Wait for some requests to complete before adding more
            if len(futures) >= 10 or not queue:
                for future in concurrent.futures.as_completed(futures):
                    warehouse_code = future.result()
                    if warehouse_code:
                        if warehouse_code not in unique_warehouses:
                            print(
                                f"Found new warehouse code: {warehouse_code} for postal code: {current_postal_code}"
                            )
                        unique_warehouses.add(warehouse_code)
                        neighbors = get_neighboring_postal_codes(current_postal_code)
                        for neighbor in neighbors:
                            if neighbor not in visited:
                                queue.append(neighbor)
                futures = []

    return unique_warehouses


# Initial postal codes to start the search
initial_postal_codes = [
    "03000",
    "03189",
    "03201",
    "03400",
    "03460",
    "03500",
    "03710",
    "03801",
    "08000",
    "08110",
    "08120",
    "08170",
    "08301",
    "08401",
    "08620",
    "08630",
    "08640",
    "08690",
    "08800",
    "08810",
    "08820",
    "08830",
    "08840",
    "08850",
    "08859",
    "08860",
    "08870",
    "08940",
    "08950",
    "08960",
    "08970",
    "08980",
    "08320",
    "13000",
    "13300",
    "13500",
    "13600",
    "18000",
    "18314",
    "18412",
    "18140",
    "18697",
    "18690",
    "25000",
    "25220",
    "25250",
    "01176",
    "28000",
    "28000",
    "28100",
    "28120",
    "28120",
    "28220",
    "28223",
    "28230",
    "28300",
    "28320",
    "28340",
    "28400",
    "28500",
    "28520",
    "28600",
    "28660",
    "28670",
    "28690",
    "28760",
    "28800",
    "28820",
    "28830",
    "28850",
    "28900",
    "28910",
    "28920",
    "28930",
    "28940",
    "28940",
    "28980",
    "29000",
    "29120",
    "29130",
    "29170",
    "29180",
    "29194",
    "29194",
    "29195",
    "29197",
    "29400",
    "29480",
    "29490",
    "29600",
    "29600",
    "29610",
    "29620",
    "29630",
    "29631",
    "29639",
    "29641",
    "29640",
    "29649",
    "29649",
    "29650",
    "29660",
    "29660",
    "29670",
    "29678",
    "29678",
    "29679",
    "29680",
    "29688",
    "29688",
    "29688",
    "29688",
    "29689",
    "29690",
    "29691",
    "29692",
    "29692",
    "29692",
    "29693",
    "29693",
    "29693",
    "29700",
    "29710",
    "29711",
    "29712",
    "29714",
    "29715",
    "29716",
    "29717",
    "29718",
    "29718",
    "29718",
    "29718",
    "29719",
    "29719",
    "29730",
    "29740",
    "29750",
    "29751",
    "29752",
    "29753",
    "29754",
    "29755",
    "29770",
    "29780",
    "29787",
    "29788",
    "29791",
    "30000",
    "30550",
    "30840",
    "30201",
    "30800",
    "30510",
    "30520",
    "35000",
    "35011",
    "35017",
    "35500",
    "35508",
    "35510",
    "35520",
    "35521",
    "35530",
    "35531",
    "35550",
    "35551",
    "35560",
    "35561",
    "35570",
    "35571",
    "35572",
    "35573",
    "35600",
    "35628",
    "35629",
    "35630",
    "35631",
    "35637",
    "35638",
    "35640",
    "35641",
    "37000",
    "37789",
    "38000",
    "38000",
    "46000",
    "46000",
    "46100",
    "46200",
    "46300",
    "46400",
    "46410",
    "46420",
    "46500",
    "46600",
    "46700",
    "46710",
    "46800",
    "46900",
    "46901",
    "46920",
    "46980",
    "48000",
    "48001",
    "48003",
    "48100",
    "48110",
    "48111",
    "48112",
    "48113",
    "48114",
    "48115",
    "48116",
    "48120",
    "48130",
    "48140",
    "48141",
    "48142",
    "48143",
    "48144",
    "48145",
    "48150",
    "48160",
    "48170",
    "48180",
    "48190",
    "48191",
    "48192",
    "48195",
    "48196",
    "48200",
    "48210",
    "48211",
    "48212",
    "48213",
    "48215",
    "48220",
    "48230",
    "48240",
    "48240",
    "48250",
    "48260",
    "48269",
    "48270",
    "48277",
    "48280",
    "48287",
    "48288",
    "48289",
    "48291",
    "48300",
    "48309",
    "48310",
    "48311",
    "48312",
    "48313",
    "48314",
    "48315",
    "48320",
    "48330",
    "48340",
    "48350",
    "48360",
    "48370",
    "48380",
    "48381",
    "48382",
    "48383",
    "48390",
    "48392",
    "48393",
    "48394",
    "48395",
    "48410",
    "48450",
    "48460",
    "48480",
    "48490",
    "48498",
    "48499",
    "48500",
    "48508",
    "48510",
    "48530",
    "48550",
    "48600",
    "48610",
    "48620",
    "48630",
    "48640",
    "48650",
    "48700",
    "48710",
    "48800",
    "48810",
    "48820",
    "48830",
    "48850",
    "48879",
    "48880",
    "48890",
    "48895",
    "48901",
    "48910",
    "48920",
    "48930",
    "48940",
    "48950",
    "48960",
    "48970",
    "48980",
    "48991",
    "51000",
    "51001",
    "52000",
    "52000",
]  # Example initial postal codes covering more areas

print("Starting the search for unique warehouse codes...")
unique_warehouses = find_unique_warehouses(initial_postal_codes)
print(f"Unique warehouse codes found: {unique_warehouses}")
