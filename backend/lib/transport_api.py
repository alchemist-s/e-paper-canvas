#!/usr/bin/python
# -*- coding:utf-8 -*-
"""
Transport for NSW API Interface
Provides a Python interface to the Transport for NSW Trip Planner API
"""

import requests
import json
from typing import List, Dict, Optional, Any
from datetime import datetime, timedelta
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TransportNSWAPI:
    """Interface for Transport for NSW Trip Planner API"""

    def __init__(
        self, api_key: str, base_url: str = "https://api.transport.nsw.gov.au/v1/tp"
    ):
        """
        Initialize the Transport NSW API client

        Args:
            api_key: Your Transport NSW API key
            base_url: Base URL for the API (defaults to production)
        """
        self.api_key = api_key
        self.base_url = base_url
        self.session = requests.Session()
        self.session.headers.update(
            {"Authorization": f"apikey {api_key}", "Content-Type": "application/json"}
        )

    def get_departures(
        self,
        stop_id: str,
        exclude_modes: Optional[List[int]] = None,
        date: Optional[datetime] = None,
        time: Optional[str] = None,
        max_results: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Get departures from a specific stop (uses departure monitor endpoint)

        Args:
            stop_id: The stop ID to get departures for
            exclude_modes: List of transport modes to exclude (1=train, 2=metro, 4=light rail, 5=bus, 7=coach, 9=ferry, 11=school bus)
            date: Date for departures (defaults to current date)
            time: Time in HHMM format (defaults to current time)
            max_results: Maximum number of results to return

        Returns:
            Dictionary containing departure information
        """
        return self.get_departures_via_departure_monitor(
            stop_id,
            exclude_modes=exclude_modes,
            date=date,
            time=time,
            max_results=max_results,
        )

    def get_departures_via_departure_mon(
        self,
        stop_id: str,
        exclude_modes: Optional[List[int]] = None,
        date: Optional[datetime] = None,
        time: Optional[str] = None,
        max_results: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Get departures from a specific stop using the departure_mon endpoint (legacy method)

        Args:
            stop_id: The stop ID to get departures for
            exclude_modes: List of transport modes to exclude (1=train, 2=metro, 4=light rail, 5=bus, 7=coach, 9=ferry, 11=school bus)
            date: Date for departures (defaults to current date)
            time: Time in HHMM format (defaults to current time)
            max_results: Maximum number of results to return

        Returns:
            Dictionary containing departure information
        """
        # Build query parameters
        params = {
            "outputFormat": "rapidJSON",
            "coordOutputFormat": "EPSG:4326",
            "mode": "direct",
            "type_dm": "stop",
            "name_dm": stop_id,
            "departureMonitorMacro": "true",
            "TfNSWDM": "true",
            "version": "10.2.1.42",
        }

        # Add date if specified
        if date:
            params["itdDate"] = date.strftime("%Y%m%d")

        # Add time if specified
        if time:
            params["itdTime"] = time

        # Add transport mode exclusions
        if exclude_modes:
            params["excludedMeans"] = "checkbox"
            for mode in exclude_modes:
                if mode in [1, 2, 4, 5, 7, 9, 11]:  # Valid transport modes
                    params[f"exclMOT_{mode}"] = "1"

        # Make the API request
        url = f"{self.base_url}/departure_mon"

        try:
            logger.info(f"Requesting departures for stop {stop_id}")
            response = self.session.get(url, params=params)
            response.raise_for_status()

            data = response.json()
            logger.info(
                f"Successfully retrieved {len(data.get('stopEvents', []))} departures"
            )

            return data

        except requests.exceptions.RequestException as e:
            logger.error(f"API request failed: {e}")
            raise
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response: {e}")
            raise

    def get_train_departures(
        self, stop_id: str, date: Optional[datetime] = None, time: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get only train departures from a specific stop

        Args:
            stop_id: The stop ID to get train departures for
            date: Date for departures (defaults to current date)
            time: Time in HHMM format (defaults to current time)

        Returns:
            Dictionary containing train departure information
        """
        # Exclude all modes except trains (mode 1)
        exclude_modes = [
            2,
            4,
            5,
            7,
            9,
            11,
        ]  # metro, light rail, bus, coach, ferry, school bus
        return self.get_departures(
            stop_id, exclude_modes=exclude_modes, date=date, time=time
        )

    def get_bus_departures(
        self, stop_id: str, date: Optional[datetime] = None, time: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get only bus departures from a specific stop

        Args:
            stop_id: The stop ID to get bus departures for
            date: Date for departures (defaults to current date)
            time: Time in HHMM format (defaults to current time)

        Returns:
            Dictionary containing bus departure information
        """
        # Exclude all modes except buses (mode 5)
        exclude_modes = [
            1,
            2,
            4,
            7,
            9,
            11,
        ]  # train, metro, light rail, coach, ferry, school bus
        return self.get_departures(
            stop_id, exclude_modes=exclude_modes, date=date, time=time
        )

    def find_stop(self, search_term: str, stop_type: str = "any") -> Dict[str, Any]:
        """
        Find stops matching a search term

        Args:
            search_term: Term to search for (stop name, ID, or coordinates)
            stop_type: Type of stop to search for (any, stop, coord, poi)

        Returns:
            Dictionary containing matching stops
        """
        params = {
            "outputFormat": "rapidJSON",
            "type_sf": stop_type,
            "name_sf": search_term,
            "coordOutputFormat": "EPSG:4326",
            "TfNSWSF": "true",
            "version": "10.2.1.42",
        }

        url = f"{self.base_url}/stop_finder"

        try:
            logger.info(f"Searching for stops matching '{search_term}'")
            response = self.session.get(url, params=params)
            response.raise_for_status()

            data = response.json()
            logger.info(f"Found {len(data.get('locations', []))} matching stops")

            return data

        except requests.exceptions.RequestException as e:
            logger.error(f"API request failed: {e}")
            raise
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response: {e}")
            raise

    def get_service_alerts(
        self,
        date: Optional[datetime] = None,
        modes: Optional[List[int]] = None,
        stop_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Get service alerts and additional information

        Args:
            date: Date for alerts (defaults to current date)
            modes: List of transport modes to filter by
            stop_id: Specific stop ID to filter alerts for

        Returns:
            Dictionary containing service alert information
        """
        params = {"outputFormat": "rapidJSON", "version": "10.2.1.42"}

        if date:
            params["filterDateValid"] = date.strftime("%d-%m-%Y")

        if modes:
            for mode in modes:
                if mode in [1, 2, 4, 5, 7, 9, 11]:
                    params["filterMOTType"] = mode

        if stop_id:
            params["itdLPxx_selStop"] = stop_id

        url = f"{self.base_url}/add_info"

        try:
            logger.info("Requesting service alerts")
            response = self.session.get(url, params=params)
            response.raise_for_status()

            data = response.json()
            logger.info(f"Retrieved service alerts")

            return data

        except requests.exceptions.RequestException as e:
            logger.error(f"API request failed: {e}")
            raise
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response: {e}")
            raise

    def format_departure_time(self, departure_time: str) -> str:
        """
        Format departure time for display

        Args:
            departure_time: ISO format time string

        Returns:
            Formatted time string
        """
        try:
            dt = datetime.fromisoformat(departure_time.replace("Z", "+00:00"))
            return dt.strftime("%H:%M")
        except:
            return departure_time

    def get_departures_summary(
        self, stop_id: str, exclude_modes: Optional[List[int]] = None
    ) -> List[Dict[str, Any]]:
        """
        Get a simplified summary of departures

        Args:
            stop_id: The stop ID to get departures for
            exclude_modes: List of transport modes to exclude

        Returns:
            List of simplified departure dictionaries
        """
        data = self.get_departures(stop_id, exclude_modes=exclude_modes)

        summary = []
        for event in data.get("stopEvents", []):
            departure = {
                "time_planned": self.format_departure_time(
                    event.get("departureTimePlanned", "")
                ),
                "time_estimated": self.format_departure_time(
                    event.get("departureTimeEstimated", "")
                ),
                "line": event.get("transportation", {}).get("number", ""),
                "destination": event.get("transportation", {})
                .get("destination", {})
                .get("name", ""),
                "mode": event.get("transportation", {})
                .get("product", {})
                .get("name", ""),
                "is_realtime": event.get("transportation", {}).get(
                    "isRealtimeControlled", False
                ),
            }
            summary.append(departure)

        return summary

    def get_departures_via_trip(
        self,
        stop_id: str,
        exclude_modes: Optional[List[int]] = None,
        date: Optional[datetime] = None,
        time: Optional[str] = None,
        max_results: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Get departures from a specific stop using the trip endpoint

        Args:
            stop_id: The stop ID to get departures for
            exclude_modes: List of transport modes to exclude (1=train, 2=metro, 4=light rail, 5=bus, 7=coach, 9=ferry, 11=school bus)
            date: Date for departures (defaults to current date)
            time: Time in HHMM format (defaults to current time)
            max_results: Maximum number of results to return

        Returns:
            Dictionary containing departure information
        """
        # Build query parameters for trip endpoint based on API specification
        params = {
            "outputFormat": "rapidJSON",
            "coordOutputFormat": "EPSG:4326",
            "depArrMacro": "dep",  # Departure-based search
            "type_origin": "any",
            "name_origin": stop_id,
            "type_destination": "any",
            "name_destination": "any",
            "TfNSWTR": "true",  # Enable Transport NSW Trip Planner features
            "version": "10.2.1.42",
        }

        # Add date if specified
        if date:
            params["itdDate"] = date.strftime("%Y%m%d")

        # Add time if specified
        if time:
            params["itdTime"] = time

        # Add maximum number of trips if specified
        if max_results:
            params["calcNumberOfTrips"] = max_results

        # Add transport mode exclusions
        if exclude_modes:
            params["excludedMeans"] = "checkbox"
            for mode in exclude_modes:
                if mode in [1, 2, 4, 5, 7, 9, 11]:  # Valid transport modes
                    params[f"exclMOT_{mode}"] = "1"

        # Make the API request
        url = f"{self.base_url}/trip"

        try:
            logger.info(f"Requesting departures for stop {stop_id} via trip endpoint")
            response = self.session.get(url, params=params)
            response.raise_for_status()

            data = response.json()

            # Extract stopEvents from the trip response
            # The trip endpoint returns journeys, but we want to extract the stopEvents
            # which contain the departure information
            stop_events = []
            for journey in data.get("journeys", []):
                for leg in journey.get("legs", []):
                    if leg.get("origin") and leg.get("origin").get("id") == stop_id:
                        # Create a stopEvent-like structure from the leg
                        stop_event = {
                            "location": leg.get("origin"),
                            "departureTimePlanned": leg.get("origin", {}).get(
                                "departureTimePlanned"
                            ),
                            "departureTimeEstimated": leg.get("origin", {}).get(
                                "departureTimeEstimated"
                            ),
                            "transportation": leg.get("transportation"),
                            "isRealtimeControlled": leg.get(
                                "isRealtimeControlled", False
                            ),
                            "infos": leg.get("infos", []),
                            "properties": leg.get("properties", {}),
                        }
                        stop_events.append(stop_event)

            # Create a response structure similar to departure_mon
            result = {
                "version": data.get("version"),
                "locations": [{"id": stop_id, "name": f"Stop {stop_id}"}],
                "stopEvents": stop_events,
            }

            logger.info(f"Successfully retrieved {len(stop_events)} departures")

            return result

        except requests.exceptions.RequestException as e:
            logger.error(f"API request failed: {e}")
            raise
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response: {e}")
            raise

    def get_departures_summary_via_trip(
        self, stop_id: str, exclude_modes: Optional[List[int]] = None
    ) -> List[Dict[str, Any]]:
        """
        Get a simplified summary of departures using the trip endpoint

        Args:
            stop_id: The stop ID to get departures for
            exclude_modes: List of transport modes to exclude

        Returns:
            List of simplified departure dictionaries
        """
        data = self.get_departures_via_trip(stop_id, exclude_modes=exclude_modes)

        summary = []
        for event in data.get("stopEvents", []):
            departure = {
                "time_planned": self.format_departure_time(
                    event.get("departureTimePlanned", "")
                ),
                "time_estimated": self.format_departure_time(
                    event.get("departureTimeEstimated", "")
                ),
                "line": event.get("transportation", {}).get("number", ""),
                "destination": event.get("transportation", {})
                .get("destination", {})
                .get("name", ""),
                "mode": event.get("transportation", {})
                .get("product", {})
                .get("name", ""),
                "is_realtime": event.get("isRealtimeControlled", False),
                "platform": event.get("location", {})
                .get("properties", {})
                .get("platform", ""),
                "wheelchair_access": event.get("properties", {}).get(
                    "WheelchairAccess", "false"
                )
                == "true",
            }
            summary.append(departure)

        return summary

    def get_departures_via_departure_monitor(
        self,
        stop_id: str,
        exclude_modes: Optional[List[int]] = None,
        date: Optional[datetime] = None,
        time: Optional[str] = None,
        max_results: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Get departures from a specific stop using the departure_mon endpoint
        This endpoint is specifically designed for departure boards

        Args:
            stop_id: The stop ID to get departures for
            exclude_modes: List of transport modes to exclude (1=train, 2=metro, 4=light rail, 5=bus, 7=coach, 9=ferry, 11=school bus)
            date: Date for departures (defaults to current date)
            time: Time in HHMM format (defaults to current time)
            max_results: Maximum number of results to return

        Returns:
            Dictionary containing departure information
        """
        # Build query parameters for departure monitor endpoint
        params = {
            "outputFormat": "rapidJSON",
            "coordOutputFormat": "EPSG:4326",
            "mode": "direct",
            "type_dm": "stop",
            "name_dm": stop_id,
            "departureMonitorMacro": "true",
            "TfNSWDM": "true",
            "version": "10.2.1.42",
        }

        # Add date if specified
        if date:
            params["itdDate"] = date.strftime("%Y%m%d")

        # Add time if specified
        if time:
            params["itdTime"] = time

        # Add transport mode exclusions
        if exclude_modes:
            params["excludedMeans"] = "checkbox"
            for mode in exclude_modes:
                if mode in [1, 2, 4, 5, 7, 9, 11]:  # Valid transport modes
                    params[f"exclMOT_{mode}"] = "1"

        # Make the API request
        url = f"{self.base_url}/departure_mon"

        try:
            logger.info(
                f"Requesting departures for stop {stop_id} via departure monitor"
            )
            response = self.session.get(url, params=params)
            response.raise_for_status()

            data = response.json()
            logger.info(
                f"Successfully retrieved {len(data.get('stopEvents', []))} departures"
            )

            return data

        except requests.exceptions.RequestException as e:
            logger.error(f"API request failed: {e}")
            raise
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response: {e}")
            raise

    def get_journey_stops(
        self,
        origin_stop_id: str,
        destination_stop_id: str,
        date: Optional[datetime] = None,
        time: Optional[str] = None,
        max_journeys: int = 1,
    ) -> List[Dict[str, Any]]:
        """
        Get a journey between two stops and extract all intermediate stops with timing

        Args:
            origin_stop_id: The origin stop ID (e.g., "213891" for Rhodes)
            destination_stop_id: The destination stop ID (e.g., "10101100" for Central)
            date: Date for journey (defaults to current date)
            time: Time in HHMM format (defaults to current time)
            max_journeys: Maximum number of journeys to return (default: 1)

        Returns:
            List of dictionaries containing stop information with timing
        """
        # Build query parameters for trip endpoint
        params = {
            "outputFormat": "rapidJSON",
            "coordOutputFormat": "EPSG:4326",
            "depArrMacro": "dep",  # Departure-based search
            "type_origin": "any",
            "name_origin": origin_stop_id,
            "type_destination": "any",
            "name_destination": destination_stop_id,
            "calcNumberOfTrips": max_journeys,
            "TfNSWTR": "true",  # Enable Transport NSW Trip Planner features
            "version": "10.2.1.42",
        }

        # Add date if specified
        if date:
            params["itdDate"] = date.strftime("%Y%m%d")

        # Add time if specified
        if time:
            params["itdTime"] = time

        # Make the API request
        url = f"{self.base_url}/trip"

        try:
            logger.info(
                f"Requesting journey from {origin_stop_id} to {destination_stop_id}"
            )
            response = self.session.get(url, params=params)
            response.raise_for_status()

            data = response.json()

            journey_stops = []

            # Process each journey
            for journey in data.get("journeys", []):
                journey_info = {
                    "journey_id": len(journey_stops) + 1,
                    "legs": [],
                    "total_duration": 0,
                    "total_distance": 0,
                }

                # Process each leg of the journey
                for leg in journey.get("legs", []):
                    transportation = leg.get("transportation", {})
                    leg_info = {
                        "transport_mode": transportation.get("product", {}).get(
                            "name", "Unknown"
                        ),
                        "line": transportation.get("number", ""),
                        "operator": transportation.get("operator", {}).get("name", ""),
                        "duration": leg.get("duration", 0),  # in seconds
                        "distance": leg.get("distance", 0),  # in meters
                        "is_realtime": leg.get("isRealtimeControlled", False),
                        "stops": [],
                        # Add destination information from transportation object
                        "destination": transportation.get("destination"),
                        "transportation": transportation,
                    }

                    # Extract all stops in this leg
                    for stop in leg.get("stopSequence", []):
                        stop_info = {
                            "id": stop.get("id", ""),
                            "name": stop.get("name", ""),
                            "type": stop.get("type", ""),
                            "coord": stop.get("coord", []),
                            "arrival_time_planned": stop.get("arrivalTimePlanned"),
                            "arrival_time_estimated": stop.get("arrivalTimeEstimated"),
                            "departure_time_planned": stop.get("departureTimePlanned"),
                            "departure_time_estimated": stop.get(
                                "departureTimeEstimated"
                            ),
                            "wheelchair_access": stop.get("properties", {}).get(
                                "WheelchairAccess", "false"
                            )
                            == "true",
                        }

                        # Calculate time in minutes for display
                        departure_time_to_use = (
                            stop_info["departure_time_estimated"]
                            or stop_info["departure_time_planned"]
                        )
                        arrival_time_to_use = (
                            stop_info["arrival_time_estimated"]
                            or stop_info["arrival_time_planned"]
                        )

                        if departure_time_to_use:
                            try:
                                dep_time = datetime.fromisoformat(
                                    departure_time_to_use.replace("Z", "+00:00")
                                )
                                current_time = datetime.now(dep_time.tzinfo)
                                time_diff = dep_time - current_time
                                stop_info["minutes_from_now"] = int(
                                    time_diff.total_seconds() / 60
                                )
                            except Exception as e:
                                logger.warning(
                                    f"Failed to calculate minutes_from_now for stop {stop_info['name']}: {e}"
                                )
                                stop_info["minutes_from_now"] = None
                        elif arrival_time_to_use:
                            # For destination stops that only have arrival times
                            try:
                                arr_time = datetime.fromisoformat(
                                    arrival_time_to_use.replace("Z", "+00:00")
                                )
                                current_time = datetime.now(arr_time.tzinfo)
                                time_diff = arr_time - current_time
                                stop_info["minutes_from_now"] = int(
                                    time_diff.total_seconds() / 60
                                )
                            except Exception as e:
                                logger.warning(
                                    f"Failed to calculate arrival minutes_from_now for stop {stop_info['name']}: {e}"
                                )
                                stop_info["minutes_from_now"] = None
                        else:
                            stop_info["minutes_from_now"] = None

                        leg_info["stops"].append(stop_info)

                    journey_info["legs"].append(leg_info)
                    journey_info["total_duration"] += leg_info["duration"]
                    journey_info["total_distance"] += leg_info["distance"]

                journey_stops.append(journey_info)

            logger.info(
                f"Successfully retrieved {len(journey_stops)} journeys with stops"
            )
            return journey_stops

        except requests.exceptions.RequestException as e:
            logger.error(f"API request failed: {e}")
            raise
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response: {e}")
            raise

    def get_simplified_journey_stops(
        self,
        origin_stop_id: str,
        destination_stop_id: str,
        date: Optional[datetime] = None,
        time: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Get a simplified list of all stops between origin and destination with timing

        Args:
            origin_stop_id: The origin stop ID (e.g., "213891" for Rhodes)
            destination_stop_id: The destination stop ID (e.g., "10101100" for Central)
            date: Date for journey (defaults to current date)
            time: Time in HHMM format (defaults to current time)

        Returns:
            List of dictionaries containing simplified stop information
        """
        journeys = self.get_journey_stops(
            origin_stop_id, destination_stop_id, date, time, max_journeys=1
        )

        if not journeys:
            return []

        # Take the first journey and flatten all stops
        all_stops = []
        journey = journeys[0]

        for leg in journey["legs"]:
            for stop in leg["stops"]:
                stop_summary = {
                    "name": stop["name"],
                    "id": stop["id"],
                    "departure_time": stop["departure_time_estimated"]
                    or stop["departure_time_planned"],
                    "arrival_time": stop["arrival_time_estimated"]
                    or stop["arrival_time_planned"],
                    "minutes_from_now": stop["minutes_from_now"],
                    "transport_mode": leg["transport_mode"],
                    "line": leg["line"],
                    "is_realtime": leg["is_realtime"],
                    # Add destination information from the leg's transportation object
                    "destination": leg.get("destination"),
                    "transportation": leg.get("transportation"),
                    "location": stop.get("location"),
                }
                all_stops.append(stop_summary)

        return all_stops


# Example usage and testing
if __name__ == "__main__":
    # Example usage (you'll need to provide your own API key)
    API_KEY = "your_api_key_here"

    # Initialize the API client
    api = TransportNSWAPI(API_KEY)

    # Example: Get train departures from Rhodes Platform 1
    try:
        # Get all train departures using the departure monitor endpoint (recommended for departure boards)
        train_departures = api.get_train_departures("213891")
        print(
            "Train departures (departure monitor):",
            json.dumps(train_departures, indent=2),
        )

        # Get simplified summary using departure monitor endpoint
        summary = api.get_departures_summary(
            "213891", exclude_modes=[2, 4, 5, 7, 9, 11]
        )
        print("Departure summary (departure monitor):", json.dumps(summary, indent=2))

        # NEW: Get journey from Rhodes to Central with all intermediate stops
        print("\n=== Rhodes to Central Journey ===")
        journey_stops = api.get_journey_stops("213891", "10101100")
        print("Full journey details:", json.dumps(journey_stops, indent=2))

        # Get simplified list of stops
        simplified_stops = api.get_simplified_journey_stops("213891", "10101100")
        print("\nSimplified stops list:")
        for i, stop in enumerate(simplified_stops):
            time_info = (
                f"{stop['minutes_from_now']} min"
                if stop["minutes_from_now"] is not None
                else "N/A"
            )
            print(
                f"{i+1}. {stop['name']} - {stop['departure_time']} ({time_info}) - {stop['transport_mode']} {stop['line']}"
            )

        # Alternative: Use the trip endpoint for journey planning
        trip_departures = api.get_departures_via_trip("213891")
        print("Trip departures:", json.dumps(trip_departures, indent=2))

        # Get simplified summary using trip endpoint
        trip_summary = api.get_departures_summary_via_trip(
            "213891", exclude_modes=[2, 4, 5, 7, 9, 11]
        )
        print("Departure summary (trip endpoint):", json.dumps(trip_summary, indent=2))

    except Exception as e:
        print(f"Error: {e}")
