import asyncio
from ably import AblyRealtime


class Chat:
    def __init__(self) -> None:
        self.__api_key = "joxgBA.oqOVUA:ZOhDkrWFtLzQh4kT0zdngPA_eOJx634Ld2Ehkd4LY1Q"
        self.client = self.__create_client()
        self.channel = None

    async def connect_to_channel( self, channel_name):
        """Connect the client to a channel"""
        
        channel = await self.client.channels.get(channel_name)
        self.channel = channel
        await channel.subscribe(self.__on_message)

    async def send_response(self, answer):
        """Sends the client answer"""
        channel =  self.client.channels.get("testChannel")
        await channel.publish("message", answer)


    def __on_message( self , message):
        return message.data
    
    def __create_client(self):
        """Creates a client instance and returns it"""
        return AblyRealtime(self.__api_key)



