/***
*
*	Copyright (c) 1996-2001, Valve LLC. All rights reserved.
*	
*	This product contains software technology licensed from Id 
*	Software, Inc. ("Id Technology").  Id Technology (c) 1996 Id Software, Inc. 
*	All Rights Reserved.
*
*   Use, distribution, and modification of this source code and/or resulting
*   object code is restricted to non-commercial enhancements to products from
*   Valve LLC.  All other use, distribution, or modification is prohibited
*   without written permission from Valve LLC.
*
****/
//
//  cdll_dll.h

// this file is included by both the game-dll and the client-dll,

#ifndef CDLL_DLL_H
#define CDLL_DLL_H

#define MAX_WEAPONS 64 // OP4-MERGE
#define MAX_WEAPON_NAME 128

#define MAX_WEAPON_POSITIONS 10 // this is the max number of weapon items in each bucket on a client
#define MAX_WEAPON_SLOTS     7 // hud item selection slots on a client (OP4 bucket 6)
#define MAX_ITEM_TYPES       6 // weapont item slots on a server

#define MAX_ITEMS 5 // hard coded item types

#define HIDEHUD_WEAPONS    (1 << 0)
#define HIDEHUD_FLASHLIGHT (1 << 1)
#define HIDEHUD_ALL        (1 << 2)
#define HIDEHUD_HEALTH     (1 << 3)

#define MAX_AMMO_TYPES 32 // ???
#define MAX_AMMO_SLOTS 32 // not really slots

#define HUD_PRINTNOTIFY  1
#define HUD_PRINTCONSOLE 2
#define HUD_PRINTTALK    3
#define HUD_PRINTCENTER  4

#define WEAPON_SUIT 31

/* OP4-MERGE: WeaponId from halflife-op4-updated dlls/cdll_dll.h */
enum WeaponId
{
	WEAPON_NONE = 0,
	WEAPON_CROWBAR,
	WEAPON_GLOCK,
	WEAPON_PYTHON,
	WEAPON_MP5,
	WEAPON_CHAINGUN,
	WEAPON_CROSSBOW,
	WEAPON_SHOTGUN,
	WEAPON_RPG,
	WEAPON_GAUSS,
	WEAPON_EGON,
	WEAPON_HORNETGUN,
	WEAPON_HANDGRENADE,
	WEAPON_TRIPMINE,
	WEAPON_SATCHEL,
	WEAPON_SNARK,
	WEAPON_GRAPPLE,
	WEAPON_EAGLE,
	WEAPON_PIPEWRENCH,
	WEAPON_M249,
	WEAPON_DISPLACER,
	WEAPON_UNUSED_21, /* ID 21 is reserved by the stock OP4 server (no GetItemInfo); keeps Shock/Spore/Sniper/Knife/Penguin at their stock IDs */
	WEAPON_SHOCKRIFLE,
	WEAPON_SPORELAUNCHER,
	WEAPON_SNIPERRIFLE,
	WEAPON_KNIFE,
	WEAPON_PENGUIN
};
/* END OP4-MERGE */


enum
{
	MAX_PLAYERS = 64,
	MAX_PLAYER_NAME = 32,
	MAX_TEAMS = 64,
	MAX_TEAM_NAME = 16,
	MAX_TEAM_DISPLAY_NAME = 32, // Extended from 16 chars in HL to 32 chars
	MAX_STEAMID = 32 // 0:0:4294967295, STEAM_ID_PENDING
};

#endif
